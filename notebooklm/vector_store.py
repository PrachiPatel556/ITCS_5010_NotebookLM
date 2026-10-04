"""Persistent Chroma vector storage for notebook chunks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence


COLLECTION_NAME = "notebook_chunks_v1"


class ChromaVectorStore:
    """Store chunk text, metadata, and embeddings in one Chroma collection."""

    def __init__(self, path: str | Path | None = None, client: Any | None = None,
                 collection_name: str = COLLECTION_NAME) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "Install the project requirements to enable ChromaDB retrieval."
            ) from exc

        if client is None:
            if path is None:
                raise ValueError("A Chroma persistence path is required")
            storage_path = Path(path)
            storage_path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=str(storage_path))

        self.client = client
        self.collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=None,
            configuration={"hnsw": {"space": "cosine"}},
        )

    @staticmethod
    def _notebook_filter(notebook_id: str) -> dict[str, Any]:
        return {"notebook_id": {"$eq": notebook_id}}

    @staticmethod
    def _enabled_filter(notebook_id: str) -> dict[str, Any]:
        return {
            "$and": [
                {"notebook_id": {"$eq": notebook_id}},
                {"enabled": {"$eq": True}},
            ]
        }

    @staticmethod
    def _metadata(chunk: dict[str, Any]) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "notebook_id": str(chunk["notebook_id"]),
            "source_id": str(chunk["source_id"]),
            "source_name": str(chunk["source_name"]),
            "source_kind": str(chunk["source_kind"]),
            "chunk_index": int(chunk["chunk_index"]),
            "enabled": bool(chunk.get("source_enabled", True)),
        }
        if chunk.get("source_uri"):
            metadata["source_uri"] = str(chunk["source_uri"])
        return metadata

    def add_chunks(self, chunks: Sequence[dict[str, Any]],
                   embeddings: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(embeddings) or not chunks:
            raise ValueError("Each nonempty chunk must have one embedding")
        self.collection.upsert(
            ids=[str(chunk["id"]) for chunk in chunks],
            documents=[str(chunk["text"]) for chunk in chunks],
            embeddings=[list(map(float, embedding)) for embedding in embeddings],
            metadatas=[self._metadata(chunk) for chunk in chunks],
        )

    def sync_notebook(
        self,
        notebook_id: str,
        chunks: Sequence[dict[str, Any]],
        embedder: Callable[[Sequence[str]], Sequence[Sequence[float]]],
    ) -> None:
        """Repair missing, stale, or changed index entries from stored source metadata."""
        existing = self.collection.get(
            where=self._notebook_filter(notebook_id),
            include=["metadatas"],
        )
        existing_ids_list = list(existing.get("ids") or [])
        existing_ids = set(existing_ids_list)
        existing_metadata = {
            chunk_id: metadata
            for chunk_id, metadata in zip(
                existing_ids_list, existing.get("metadatas") or []
            )
        }
        current_ids = {str(chunk["id"]) for chunk in chunks}

        stale_ids = sorted(existing_ids - current_ids)
        if stale_ids:
            self.collection.delete(ids=stale_ids)

        present = [
            chunk for chunk in chunks
            if str(chunk["id"]) in existing_ids
            and existing_metadata.get(str(chunk["id"])) != self._metadata(chunk)
        ]
        for start in range(0, len(present), 500):
            batch = present[start:start + 500]
            self.collection.update(
                ids=[str(chunk["id"]) for chunk in batch],
                metadatas=[self._metadata(chunk) for chunk in batch],
            )

        missing = [chunk for chunk in chunks if str(chunk["id"]) not in existing_ids]
        for start in range(0, len(missing), 500):
            batch = missing[start:start + 500]
            embeddings = embedder([str(chunk["text"]) for chunk in batch])
            self.add_chunks(batch, embeddings)

    def query(self, notebook_id: str, query_embedding: Sequence[float],
              top_k: int) -> list[dict[str, Any]]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        results = self.collection.query(
            query_embeddings=[list(map(float, query_embedding))],
            n_results=top_k,
            where=self._enabled_filter(notebook_id),
            include=["documents", "metadatas", "distances"],
        )
        ids = (results.get("ids") or [[]])[0]
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        matches = []
        for chunk_id, document, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            item = dict(metadata or {})
            item.update(
                {
                    "chunk_id": str(chunk_id),
                    "text": str(document or ""),
                    "score": 1.0 - float(distance),
                }
            )
            matches.append(item)
        return matches

    def delete_source(self, source_id: str) -> None:
        self.collection.delete(where={"source_id": {"$eq": source_id}})

    def delete_notebook(self, notebook_id: str) -> None:
        self.collection.delete(where=self._notebook_filter(notebook_id))
