"""SQLite persistence for notebook data and its small, local vector index."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_db_path() -> Path:
    explicit = os.getenv("NOTEBOOKLM_DB_PATH")
    if explicit:
        return Path(explicit)
    data_dir = os.getenv("NOTEBOOKLM_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "notebooklm.db"
    space_volume = Path("/data")
    return (space_volume if space_volume.is_dir() else Path("data")) / "notebooklm.db"


class NotebookStore:
    """Notebook-scoped storage. All public methods open their own connection."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS notebooks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sources (
                    id TEXT PRIMARY KEY,
                    notebook_id TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    uri TEXT,
                    text TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sources_notebook ON sources(notebook_id);
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    notebook_id TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
                    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    UNIQUE(source_id, chunk_index)
                );
                CREATE INDEX IF NOT EXISTS idx_chunks_notebook ON chunks(notebook_id);
                CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    notebook_id TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_messages_notebook ON messages(notebook_id, created_at);
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    notebook_id TEXT NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    file_path TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_artifacts_notebook ON artifacts(notebook_id, created_at);
                """
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys = ON")
            db.execute("PRAGMA busy_timeout = 30000")
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _required(value: str, label: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{label} cannot be empty")
        return cleaned

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def get_notebook(self, notebook_id: str) -> dict[str, Any]:
        with self._connection() as db:
            row = db.execute("SELECT * FROM notebooks WHERE id = ?", (notebook_id,)).fetchone()
        if row is None:
            raise KeyError(f"Notebook {notebook_id} does not exist")
        return dict(row)

    def create_notebook(self, title: str) -> dict[str, Any]:
        now = _utc_now()
        notebook = {"id": str(uuid4()), "title": self._required(title, "Notebook title"),
                    "created_at": now, "updated_at": now}
        with self._connection() as db:
            db.execute("INSERT INTO notebooks VALUES (:id, :title, :created_at, :updated_at)", notebook)
        return notebook

    def list_notebooks(self) -> list[dict[str, Any]]:
        with self._connection() as db:
            rows = db.execute("SELECT * FROM notebooks ORDER BY updated_at DESC, created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def rename_notebook(self, notebook_id: str, title: str) -> dict[str, Any]:
        with self._connection() as db:
            cursor = db.execute("UPDATE notebooks SET title = ?, updated_at = ? WHERE id = ?",
                                (self._required(title, "Notebook title"), _utc_now(), notebook_id))
            if cursor.rowcount == 0:
                raise KeyError(f"Notebook {notebook_id} does not exist")
        return self.get_notebook(notebook_id)

    def delete_notebook(self, notebook_id: str) -> None:
        with self._connection() as db:
            cursor = db.execute("DELETE FROM notebooks WHERE id = ?", (notebook_id,))
            if cursor.rowcount == 0:
                raise KeyError(f"Notebook {notebook_id} does not exist")

    def add_source(self, notebook_id: str, name: str, kind: str, text: str,
                   chunks: Sequence[str], embeddings: Sequence[Sequence[float]],
                   uri: str | None = None) -> dict[str, Any]:
        """Atomically persist a source and every embedding; no partial source on failure."""
        if len(chunks) != len(embeddings) or not chunks:
            raise ValueError("A source must have one embedding for every nonempty chunk")
        if not text.strip():
            raise ValueError("Source contains no extractable text")
        source_id = str(uuid4())
        created_at = _utc_now()
        with self._connection() as db:
            if db.execute("SELECT 1 FROM notebooks WHERE id = ?", (notebook_id,)).fetchone() is None:
                raise KeyError(f"Notebook {notebook_id} does not exist")
            db.execute(
                "INSERT INTO sources (id, notebook_id, name, kind, uri, text, enabled, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
                (source_id, notebook_id, self._required(name, "Source name"),
                 self._required(kind, "Source type"), uri, text, created_at),
            )
            db.executemany(
                "INSERT INTO chunks (id, notebook_id, source_id, chunk_index, text, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [(str(uuid4()), notebook_id, source_id, index, chunk,
                  json.dumps([float(value) for value in embedding]))
                 for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))],
            )
            db.execute("UPDATE notebooks SET updated_at = ? WHERE id = ?", (_utc_now(), notebook_id))
        return self.get_source(source_id)

    def get_source(self, source_id: str) -> dict[str, Any]:
        with self._connection() as db:
            row = db.execute(
                "SELECT s.*, (SELECT COUNT(*) FROM chunks c WHERE c.source_id = s.id) AS chunk_count "
                "FROM sources s WHERE s.id = ?", (source_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Source {source_id} does not exist")
        result = dict(row)
        result["enabled"] = bool(result["enabled"])
        return result

    def list_sources(self, notebook_id: str) -> list[dict[str, Any]]:
        self.get_notebook(notebook_id)
        with self._connection() as db:
            rows = db.execute(
                "SELECT s.id, s.notebook_id, s.name, s.kind, s.uri, s.enabled, s.created_at, "
                "(SELECT COUNT(*) FROM chunks c WHERE c.source_id = s.id) AS chunk_count "
                "FROM sources s WHERE s.notebook_id = ? ORDER BY s.created_at DESC, s.rowid DESC",
                (notebook_id,),
            ).fetchall()
        result = [dict(row) for row in rows]
        for source in result:
            source["enabled"] = bool(source["enabled"])
        return result

    def delete_source(self, source_id: str) -> None:
        with self._connection() as db:
            cursor = db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            if cursor.rowcount == 0:
                raise KeyError(f"Source {source_id} does not exist")

    def set_source_enabled(self, source_id: str, enabled: bool) -> dict[str, Any]:
        with self._connection() as db:
            cursor = db.execute("UPDATE sources SET enabled = ? WHERE id = ?", (int(enabled), source_id))
            if cursor.rowcount == 0:
                raise KeyError(f"Source {source_id} does not exist")
        return self.get_source(source_id)

    def list_chunks(self, notebook_id: str, enabled_only: bool = True,
                    limit: int | None = None) -> list[dict[str, Any]]:
        self.get_notebook(notebook_id)
        if limit is not None and limit < 1:
            raise ValueError("Chunk limit must be positive")
        with self._connection() as db:
            rows = db.execute(
                "SELECT c.id, c.notebook_id, c.source_id, c.chunk_index, c.text, c.embedding, "
                "s.name AS source_name, s.kind AS source_kind, s.uri AS source_uri "
                "FROM chunks c JOIN sources s ON s.id = c.source_id "
                "WHERE c.notebook_id = ? AND (? = 0 OR s.enabled = 1) "
                "ORDER BY c.source_id, c.chunk_index LIMIT ?",
                (notebook_id, int(enabled_only), limit if limit is not None else -1),
            ).fetchall()
        result = [dict(row) for row in rows]
        for chunk in result:
            chunk["embedding"] = json.loads(chunk["embedding"])
        return result

    def get_notebook_text(self, notebook_id: str, enabled_only: bool = True) -> str:
        self.get_notebook(notebook_id)
        with self._connection() as db:
            rows = db.execute(
                "SELECT name, text FROM sources WHERE notebook_id = ? AND (? = 0 OR enabled = 1) "
                "ORDER BY created_at, rowid", (notebook_id, int(enabled_only))
            ).fetchall()
        return "\n\n".join(f"# {row['name']}\n\n{row['text']}" for row in rows)

    def add_message(self, notebook_id: str, role: str, content: str,
                    citations: Sequence[dict[str, Any]] | None = None) -> dict[str, Any]:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("Message role must be user, assistant, or system")
        message = {"id": str(uuid4()), "notebook_id": notebook_id, "role": role,
                   "content": self._required(content, "Message"),
                   "citations": list(citations or []), "created_at": _utc_now()}
        with self._connection() as db:
            if db.execute("SELECT 1 FROM notebooks WHERE id = ?", (notebook_id,)).fetchone() is None:
                raise KeyError(f"Notebook {notebook_id} does not exist")
            db.execute("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
                       (message["id"], notebook_id, role, message["content"],
                        json.dumps(message["citations"]), message["created_at"]))
        return message

    def list_messages(self, notebook_id: str) -> list[dict[str, Any]]:
        self.get_notebook(notebook_id)
        with self._connection() as db:
            rows = db.execute("SELECT * FROM messages WHERE notebook_id = ? ORDER BY created_at, rowid",
                              (notebook_id,)).fetchall()
        messages = [dict(row) for row in rows]
        for message in messages:
            message["citations"] = json.loads(message["citations"])
        return messages

    def add_artifact(self, notebook_id: str, kind: str, title: str, content: str,
                     file_path: str | None = None) -> dict[str, Any]:
        artifact = {"id": str(uuid4()), "notebook_id": notebook_id,
                    "kind": self._required(kind, "Artifact type"),
                    "title": self._required(title, "Artifact title"),
                    "content": self._required(content, "Artifact content"),
                    "file_path": file_path, "created_at": _utc_now()}
        with self._connection() as db:
            if db.execute("SELECT 1 FROM notebooks WHERE id = ?", (notebook_id,)).fetchone() is None:
                raise KeyError(f"Notebook {notebook_id} does not exist")
            db.execute("INSERT INTO artifacts VALUES (:id, :notebook_id, :kind, :title, :content, :file_path, :created_at)",
                       artifact)
        return artifact

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        with self._connection() as db:
            row = db.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
        if row is None:
            raise KeyError(f"Artifact {artifact_id} does not exist")
        return dict(row)

    def list_artifacts(self, notebook_id: str) -> list[dict[str, Any]]:
        self.get_notebook(notebook_id)
        with self._connection() as db:
            rows = db.execute("SELECT * FROM artifacts WHERE notebook_id = ? ORDER BY created_at DESC, rowid DESC",
                              (notebook_id,)).fetchall()
        return [dict(row) for row in rows]
