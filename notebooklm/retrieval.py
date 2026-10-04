"""Sentence-transformer embeddings and ChromaDB vector/hybrid retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Any, Sequence

from .storage import NotebookStore
from .vector_store import ChromaVectorStore


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "their", "there",
    "these", "this", "to", "was", "were", "what", "when", "where", "which",
    "who", "why", "with",
}


@lru_cache(maxsize=2)
def _model(model_name: str) -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Install sentence-transformers to enable source embeddings") from exc
    return SentenceTransformer(model_name, device="cpu")


def embed_texts(texts: Sequence[str], model_name: str = DEFAULT_MODEL) -> list[list[float]]:
    """Embed text with the same model used for both indexing and search."""
    if not texts:
        return []
    vectors = _model(model_name).encode(list(texts), normalize_embeddings=True)
    return [[float(value) for value in vector] for vector in vectors]


def _terms(text: str) -> list[str]:
    return [
        term for term in re.findall(r"\b\w+\b", text.casefold())
        if len(term) > 1 and term not in _STOP_WORDS
    ]


class Retriever:
    """Use ChromaDB semantic search with optional lexical rank fusion."""

    def __init__(self, store: NotebookStore, model_name: str = DEFAULT_MODEL,
                 vector_store: ChromaVectorStore | None = None) -> None:
        self.store = store
        self.model_name = model_name
        self.vector_store = vector_store or ChromaVectorStore(store.data_dir / "chroma")

    def sync_notebook(self, notebook_id: str) -> None:
        chunks = self.store.list_chunks(notebook_id, enabled_only=False)
        self.vector_store.sync_notebook(
            notebook_id,
            chunks,
            lambda texts: embed_texts(texts, self.model_name),
        )

    def delete_source(self, source_id: str) -> None:
        self.vector_store.delete_source(source_id)

    def delete_notebook(self, notebook_id: str) -> None:
        self.vector_store.delete_notebook(notebook_id)

    def search(self, notebook_id: str, query: str, method: str = "hybrid",
               top_k: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Question cannot be empty")
        if method not in {"vector", "hybrid"}:
            raise ValueError("Retrieval method must be 'vector' or 'hybrid'")
        if top_k < 1:
            raise ValueError("top_k must be positive")

        all_chunks = self.store.list_chunks(notebook_id, enabled_only=False)
        if not all_chunks:
            return []
        self.sync_notebook(notebook_id)
        chunks = [chunk for chunk in all_chunks if chunk["source_enabled"]]
        if not chunks:
            return []

        query_vector = embed_texts([query], self.model_name)[0]
        matches = self.vector_store.query(notebook_id, query_vector, len(chunks))
        similarities = {match["chunk_id"]: match["score"] for match in matches}
        similarities.update({
            chunk["id"]: similarities.get(chunk["id"], -1.0) for chunk in chunks
        })

        if method == "vector":
            scores = similarities
        else:
            query_terms = set(_terms(query))
            document_terms = {
                chunk["id"]: Counter(_terms(chunk["text"])) for chunk in chunks
            }
            doc_count = len(chunks)
            document_frequency = Counter(
                term
                for terms in document_terms.values()
                for term in query_terms
                if term in terms
            )
            lexical = {}
            for chunk in chunks:
                terms = document_terms[chunk["id"]]
                lexical[chunk["id"]] = sum(
                    (1.0 + math.log((doc_count + 1) / (document_frequency[term] + 1)))
                    * (terms[term] / (terms[term] + 1.2))
                    for term in query_terms
                    if terms[term]
                )
            vector_order = sorted(
                chunks,
                key=lambda chunk: similarities[chunk["id"]],
                reverse=True,
            )
            lexical_order = sorted(
                (chunk for chunk in chunks if lexical[chunk["id"]] > 0),
                key=lambda chunk: lexical[chunk["id"]],
                reverse=True,
            )
            scores = {
                chunk["id"]: 0.65 / (10 + rank)
                for rank, chunk in enumerate(vector_order, start=1)
            }
            for rank, chunk in enumerate(lexical_order, start=1):
                scores[chunk["id"]] += 0.35 / (10 + rank)

        ranked = sorted(
            chunks,
            key=lambda chunk: scores[chunk["id"]],
            reverse=True,
        )[:top_k]
        return [
            {
                "chunk_id": chunk["id"],
                "source_id": chunk["source_id"],
                "source_name": chunk["source_name"],
                "source_kind": chunk["source_kind"],
                "source_uri": chunk["source_uri"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "score": round(scores[chunk["id"]], 6),
                "citation": f"{chunk['source_name']} (chunk {chunk['chunk_index'] + 1})",
            }
            for chunk in ranked
        ]
