"""Application operations shared by the Gradio interface and evaluation script."""

from __future__ import annotations

import time
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from .generation import answer_question, create_artifact
from .ingest import ingest_file, ingest_url
from .retrieval import Retriever
from .storage import NotebookStore


class NotebookService:
    def __init__(self, store: NotebookStore | None = None, retriever: Retriever | None = None):
        self.store = store or NotebookStore()
        self.retriever = retriever or Retriever(self.store)

    def list_notebooks(self) -> list[dict]:
        return [{**row, "name": row["title"]} for row in self.store.list_notebooks()]

    def create_notebook(self, name: str) -> dict:
        name = (name or "").strip()
        if not name:
            raise ValueError("Enter a notebook name.")
        row = self.store.create_notebook(name)
        return {**row, "name": row["title"]}

    def rename_notebook(self, notebook_id: str, name: str) -> None:
        name = (name or "").strip()
        if not name:
            raise ValueError("Enter a notebook name.")
        self.store.rename_notebook(notebook_id, name)

    def delete_notebook(self, notebook_id: str) -> None:
        self.store.delete_notebook(notebook_id)
        source_folder = self._source_dir(notebook_id, create=False)
        if source_folder.exists():
            for file in source_folder.iterdir():
                if file.is_file():
                    file.unlink()
            source_folder.rmdir()
        folder = self._artifact_dir(notebook_id, create=False)
        if folder.exists():
            for file in folder.glob("*.md"):
                file.unlink()
            folder.rmdir()

    def list_sources(self, notebook_id: str) -> list[dict]:
        self._require_notebook(notebook_id)
        return self.store.list_sources(notebook_id)

    def add_files(self, notebook_id: str, paths: list[str]) -> list[dict]:
        self._require_notebook(notebook_id)
        if not paths:
            raise ValueError("Choose at least one PDF, PPTX, or TXT file.")
        results = []
        for path in paths:
            source = ingest_file(self.store, notebook_id, path)
            saved_path = self._source_dir(notebook_id) / f"{UUID(source['id']).hex}.{source['kind']}"
            try:
                shutil.copyfile(path, saved_path)
            except Exception:
                saved_path.unlink(missing_ok=True)
                self.store.delete_source(source["id"])
                raise
            results.append(source)
        return results

    def add_url(self, notebook_id: str, url: str) -> dict:
        self._require_notebook(notebook_id)
        return ingest_url(self.store, notebook_id, (url or "").strip())

    def delete_source(self, notebook_id: str, source_id: str) -> None:
        self._require_notebook(notebook_id)
        source = next((item for item in self.store.list_sources(notebook_id) if item["id"] == source_id), None)
        if source is None:
            raise ValueError("Source does not belong to this notebook.")
        if source["kind"] in {"pdf", "pptx", "txt"}:
            source_folder = self._source_dir(notebook_id, create=False)
            raw_path = source_folder / f"{UUID(source_id).hex}.{source['kind']}"
            raw_path.unlink(missing_ok=True)
            if source_folder.exists() and not any(source_folder.iterdir()):
                source_folder.rmdir()
        self.store.delete_source(source_id)

    def list_messages(self, notebook_id: str) -> list[dict]:
        self._require_notebook(notebook_id)
        return self.store.list_messages(notebook_id)

    def ask(self, notebook_id: str, question: str, method: str = "hybrid") -> dict:
        self._require_notebook(notebook_id)
        question = (question or "").strip()
        if not question:
            raise ValueError("Enter a question.")
        if method not in {"vector", "hybrid"}:
            raise ValueError("Retrieval method must be vector or hybrid.")
        chunks = self.retriever.search(notebook_id, question, method=method, top_k=5)
        history = self.store.list_messages(notebook_id)[-6:]
        answer = answer_question(question, chunks, history)
        citations = [
            {
                "source_id": chunk["source_id"],
                "source_name": chunk["source_name"],
                "chunk_id": chunk["chunk_id"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"][:800],
                "score": chunk["score"],
            }
            for chunk in chunks
        ]
        self.store.add_message(notebook_id, "user", question)
        self.store.add_message(notebook_id, "assistant", answer, citations)
        return {"answer": answer, "citations": citations}

    def _artifact_chunks(self, notebook_id: str, max_chunks: int = 60) -> list[dict]:
        rows = self.store.list_chunks(notebook_id, enabled_only=True)
        by_source: dict[str, list[dict]] = {}
        for row in rows:
            by_source.setdefault(row["source_id"], []).append(row)
        chosen = []
        while by_source and len(chosen) < max_chunks:
            for source_id in list(by_source):
                group = by_source[source_id]
                chosen.append(group.pop(0))
                if not group:
                    del by_source[source_id]
                if len(chosen) >= max_chunks:
                    break
        return chosen

    def generate_artifact(self, notebook_id: str, kind: str) -> dict:
        self._require_notebook(notebook_id)
        if kind not in {"report", "quiz"}:
            raise ValueError("Artifact kind must be report or quiz.")
        chunks = self._artifact_chunks(notebook_id)
        content = create_artifact(kind, chunks)
        title = f"{kind.title()} · {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        folder = self._artifact_dir(notebook_id)
        path = folder / f"{kind}-{uuid4().hex}.md"
        path.write_text(content, encoding="utf-8")
        try:
            artifact = self.store.add_artifact(notebook_id, kind, title, content, str(path))
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return {**artifact, "path": str(path)}

    def list_artifacts(self, notebook_id: str) -> list[dict]:
        self._require_notebook(notebook_id)
        return [{**row, "path": row.get("file_path")} for row in self.store.list_artifacts(notebook_id)]

    def compare_retrieval(self, notebook_id: str, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        self._require_notebook(notebook_id)
        question = (question or "").strip()
        if not question:
            raise ValueError("Enter an evaluation question.")
        if top_k < 1:
            raise ValueError("top_k must be positive.")
        # Warm the embedding model so the first method is not charged for model startup.
        self.retriever.search(notebook_id, question, method="vector", top_k=top_k)
        results = []
        for method in ("vector", "hybrid"):
            start = time.perf_counter()
            chunks = self.retriever.search(notebook_id, question, method=method, top_k=top_k)
            elapsed_ms = (time.perf_counter() - start) * 1000
            results.append(
                {"method": method, "latency_ms": round(elapsed_ms, 2), "chunks": chunks}
            )
        return results

    def _require_notebook(self, notebook_id: str) -> None:
        if not notebook_id:
            raise ValueError("Select an existing notebook.")
        try:
            self.store.get_notebook(notebook_id)
        except KeyError as exc:
            raise ValueError("Select an existing notebook.") from exc

    def _artifact_dir(self, notebook_id: str, create: bool = True) -> Path:
        # Notebook IDs are UUIDs; never use a user-controlled path component directly.
        safe_id = UUID(str(notebook_id)).hex
        folder = self.store.db_path.parent / "artifacts" / safe_id
        if create:
            folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _source_dir(self, notebook_id: str, create: bool = True) -> Path:
        safe_id = UUID(str(notebook_id)).hex
        folder = self.store.db_path.parent / "sources" / safe_id
        if create:
            folder.mkdir(parents=True, exist_ok=True)
        return folder
