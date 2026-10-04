"""Notebook-scoped JSON and filesystem storage."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID, uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_data_dir() -> Path:
    explicit = os.getenv("NOTEBOOKLM_DATA_DIR")
    if explicit:
        return Path(explicit)
    space_volume = Path("/data")
    return space_volume if space_volume.is_dir() else Path("data")


class NotebookStore:
    """Persist notebook metadata and extracted content without a relational database."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else _default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notebooks_dir = self.data_dir / "notebooks"
        self.notebooks_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.data_dir / "notebooks.json"
        self._lock = threading.RLock()
        if not self.index_path.exists():
            self._write_json(self.index_path, [])

    @staticmethod
    def _required(value: str, label: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{label} cannot be empty")
        return cleaned

    @staticmethod
    def _safe_id(value: str) -> str:
        try:
            return str(UUID(str(value)))
        except (TypeError, ValueError, AttributeError) as exc:
            raise KeyError(f"Invalid identifier: {value}") from exc

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read stored notebook data: {path.name}") from exc

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(
                json.dumps(value, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def _load_index(self) -> list[dict[str, Any]]:
        data = self._read_json(self.index_path)
        if not isinstance(data, list):
            raise RuntimeError("Notebook index is invalid")
        return data

    def _notebook_path(self, notebook_id: str) -> Path:
        return self.notebooks_dir / f"{self._safe_id(notebook_id)}.json"

    def _load_state(self, notebook_id: str) -> dict[str, Any]:
        path = self._notebook_path(notebook_id)
        try:
            state = self._read_json(path)
        except FileNotFoundError as exc:
            raise KeyError(f"Notebook {notebook_id} does not exist") from exc
        if not isinstance(state, dict):
            raise RuntimeError("Notebook data is invalid")
        return state

    def _save_state(self, notebook_id: str, state: dict[str, Any]) -> None:
        self._write_json(self._notebook_path(notebook_id), state)

    def _touch_index(self, notebook_id: str, title: str | None = None) -> dict[str, Any]:
        index = self._load_index()
        for notebook in index:
            if notebook["id"] == notebook_id:
                if title is not None:
                    notebook["title"] = title
                notebook["updated_at"] = _utc_now()
                self._write_json(self.index_path, index)
                return dict(notebook)
        raise KeyError(f"Notebook {notebook_id} does not exist")

    def get_notebook(self, notebook_id: str) -> dict[str, Any]:
        safe_id = self._safe_id(notebook_id)
        with self._lock:
            for notebook in self._load_index():
                if notebook["id"] == safe_id:
                    return dict(notebook)
        raise KeyError(f"Notebook {notebook_id} does not exist")

    def create_notebook(self, title: str) -> dict[str, Any]:
        now = _utc_now()
        notebook = {
            "id": str(uuid4()),
            "title": self._required(title, "Notebook title"),
            "created_at": now,
            "updated_at": now,
        }
        state = {
            "sources": [],
            "chunks": [],
            "messages": [],
            "artifacts": [],
        }
        with self._lock:
            index = self._load_index()
            self._save_state(notebook["id"], state)
            index.append(notebook)
            self._write_json(self.index_path, index)
        return dict(notebook)

    def list_notebooks(self) -> list[dict[str, Any]]:
        with self._lock:
            index = self._load_index()
        return sorted(
            (dict(notebook) for notebook in index),
            key=lambda notebook: (notebook["updated_at"], notebook["created_at"]),
            reverse=True,
        )

    def rename_notebook(self, notebook_id: str, title: str) -> dict[str, Any]:
        safe_id = self._safe_id(notebook_id)
        with self._lock:
            self._load_state(safe_id)
            return self._touch_index(safe_id, self._required(title, "Notebook title"))

    def delete_notebook(self, notebook_id: str) -> None:
        safe_id = self._safe_id(notebook_id)
        with self._lock:
            index = self._load_index()
            filtered = [notebook for notebook in index if notebook["id"] != safe_id]
            if len(filtered) == len(index):
                raise KeyError(f"Notebook {notebook_id} does not exist")
            self._write_json(self.index_path, filtered)
            self._notebook_path(safe_id).unlink(missing_ok=True)

    def add_source(self, notebook_id: str, name: str, kind: str, text: str,
                   chunks: Sequence[str], uri: str | None = None) -> dict[str, Any]:
        if not chunks:
            raise ValueError("A source must have at least one nonempty chunk")
        if not text.strip():
            raise ValueError("Source contains no extractable text")
        safe_id = self._safe_id(notebook_id)
        source_id = str(uuid4())
        source = {
            "id": source_id,
            "notebook_id": safe_id,
            "name": self._required(name, "Source name"),
            "kind": self._required(kind, "Source type"),
            "uri": uri,
            "text": text,
            "enabled": True,
            "created_at": _utc_now(),
        }
        chunk_rows = [
            {
                "id": str(uuid4()),
                "notebook_id": safe_id,
                "source_id": source_id,
                "chunk_index": index,
                "text": chunk,
            }
            for index, chunk in enumerate(chunks)
        ]
        with self._lock:
            state = self._load_state(safe_id)
            state["sources"].append(source)
            state["chunks"].extend(chunk_rows)
            self._save_state(safe_id, state)
            self._touch_index(safe_id)
        return {**source, "chunk_count": len(chunk_rows)}

    def _find_source(self, source_id: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
        safe_source_id = self._safe_id(source_id)
        for notebook in self._load_index():
            state = self._load_state(notebook["id"])
            for source in state["sources"]:
                if source["id"] == safe_source_id:
                    return notebook["id"], state, source
        raise KeyError(f"Source {source_id} does not exist")

    def get_source(self, source_id: str) -> dict[str, Any]:
        with self._lock:
            _, state, source = self._find_source(source_id)
            count = sum(1 for chunk in state["chunks"] if chunk["source_id"] == source["id"])
            return {**source, "enabled": bool(source["enabled"]), "chunk_count": count}

    def list_sources(self, notebook_id: str) -> list[dict[str, Any]]:
        safe_id = self.get_notebook(notebook_id)["id"]
        with self._lock:
            state = self._load_state(safe_id)
            sources = []
            for source in reversed(state["sources"]):
                count = sum(1 for chunk in state["chunks"] if chunk["source_id"] == source["id"])
                sources.append({
                    key: value for key, value in source.items() if key != "text"
                } | {"enabled": bool(source["enabled"]), "chunk_count": count})
            return sources

    def delete_source(self, source_id: str) -> None:
        with self._lock:
            notebook_id, state, source = self._find_source(source_id)
            state["sources"] = [
                item for item in state["sources"] if item["id"] != source["id"]
            ]
            state["chunks"] = [
                chunk for chunk in state["chunks"] if chunk["source_id"] != source["id"]
            ]
            self._save_state(notebook_id, state)
            self._touch_index(notebook_id)

    def set_source_enabled(self, source_id: str, enabled: bool) -> dict[str, Any]:
        with self._lock:
            notebook_id, state, source = self._find_source(source_id)
            source["enabled"] = bool(enabled)
            self._save_state(notebook_id, state)
            self._touch_index(notebook_id)
        return self.get_source(source_id)

    def list_chunks(self, notebook_id: str, enabled_only: bool = True,
                    limit: int | None = None) -> list[dict[str, Any]]:
        safe_id = self.get_notebook(notebook_id)["id"]
        if limit is not None and limit < 1:
            raise ValueError("Chunk limit must be positive")
        with self._lock:
            state = self._load_state(safe_id)
            sources = {source["id"]: source for source in state["sources"]}
            chunks = []
            for chunk in state["chunks"]:
                source = sources.get(chunk["source_id"])
                if source is None or (enabled_only and not source["enabled"]):
                    continue
                chunks.append({
                    **chunk,
                    "source_name": source["name"],
                    "source_kind": source["kind"],
                    "source_uri": source.get("uri"),
                    "source_enabled": bool(source["enabled"]),
                })
                if limit is not None and len(chunks) >= limit:
                    break
            return chunks

    def get_notebook_text(self, notebook_id: str, enabled_only: bool = True) -> str:
        safe_id = self.get_notebook(notebook_id)["id"]
        with self._lock:
            state = self._load_state(safe_id)
            sources = [
                source for source in state["sources"]
                if not enabled_only or source["enabled"]
            ]
        return "\n\n".join(
            f"# {source['name']}\n\n{source['text']}" for source in sources
        )

    def add_message(self, notebook_id: str, role: str, content: str,
                    citations: Sequence[dict[str, Any]] | None = None) -> dict[str, Any]:
        if role not in {"user", "assistant", "system"}:
            raise ValueError("Message role must be user, assistant, or system")
        safe_id = self.get_notebook(notebook_id)["id"]
        message = {
            "id": str(uuid4()),
            "notebook_id": safe_id,
            "role": role,
            "content": self._required(content, "Message"),
            "citations": list(citations or []),
            "created_at": _utc_now(),
        }
        with self._lock:
            state = self._load_state(safe_id)
            state["messages"].append(message)
            self._save_state(safe_id, state)
        return dict(message)

    def list_messages(self, notebook_id: str) -> list[dict[str, Any]]:
        safe_id = self.get_notebook(notebook_id)["id"]
        with self._lock:
            return [dict(message) for message in self._load_state(safe_id)["messages"]]

    def add_artifact(self, notebook_id: str, kind: str, title: str, content: str,
                     file_path: str | None = None) -> dict[str, Any]:
        safe_id = self.get_notebook(notebook_id)["id"]
        artifact = {
            "id": str(uuid4()),
            "notebook_id": safe_id,
            "kind": self._required(kind, "Artifact type"),
            "title": self._required(title, "Artifact title"),
            "content": self._required(content, "Artifact content"),
            "file_path": file_path,
            "created_at": _utc_now(),
        }
        with self._lock:
            state = self._load_state(safe_id)
            state["artifacts"].append(artifact)
            self._save_state(safe_id, state)
        return dict(artifact)

    def get_artifact(self, artifact_id: str) -> dict[str, Any]:
        safe_artifact_id = self._safe_id(artifact_id)
        with self._lock:
            for notebook in self._load_index():
                for artifact in self._load_state(notebook["id"])["artifacts"]:
                    if artifact["id"] == safe_artifact_id:
                        return dict(artifact)
        raise KeyError(f"Artifact {artifact_id} does not exist")

    def list_artifacts(self, notebook_id: str) -> list[dict[str, Any]]:
        safe_id = self.get_notebook(notebook_id)["id"]
        with self._lock:
            artifacts = self._load_state(safe_id)["artifacts"]
            return [dict(artifact) for artifact in reversed(artifacts)]
