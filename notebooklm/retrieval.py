"""Sentence-transformer embeddings and notebook-scoped vector/hybrid retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from typing import Any, Sequence

from .storage import NotebookStore


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
    return SentenceTransformer(model_name)


def embed_texts(texts: Sequence[str], model_name: str = DEFAULT_MODEL) -> list[list[float]]:
    """Embed text with the same model used for both indexing and search."""
    if not texts:
        return []
    vectors = _model(model_name).encode(list(texts), normalize_embeddings=True)
    return [[float(value) for value in vector] for vector in vectors]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Stored embedding dimensions differ from the query model")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _terms(text: str) -> list[str]:
    return [term for term in re.findall(r"\b\w+\b", text.casefold())
            if len(term) > 1 and term not in _STOP_WORDS]


class Retriever:
    """Exhaustive cosine search with an optional keyword rank-fusion approach.

    The vector index lives in SQLite as JSON arrays. Exhaustive scoring is a good
    fit for modest class-project notebooks and requires no external vector service.
    """

    def __init__(self, store: NotebookStore, model_name: str = DEFAULT_MODEL) -> None:
        self.store = store
        self.model_name = model_name

    def search(self, notebook_id: str, query: str, method: str = "hybrid",
               top_k: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            raise ValueError("Question cannot be empty")
        if method not in {"vector", "hybrid"}:
            raise ValueError("Retrieval method must be 'vector' or 'hybrid'")
        if top_k < 1:
            raise ValueError("top_k must be positive")

        chunks = self.store.list_chunks(notebook_id, enabled_only=True)
        if not chunks:
            return []
        query_vector = embed_texts([query], self.model_name)[0]
        similarities = {chunk["id"]: _cosine(query_vector, chunk["embedding"])
                        for chunk in chunks}

        if method == "vector":
            scores = similarities
        else:
            # Reciprocal rank fusion combines semantic matches with exact terms.
            # Only chunks with a lexical match receive a keyword contribution.
            query_terms = set(_terms(query))
            document_terms = {chunk["id"]: Counter(_terms(chunk["text"])) for chunk in chunks}
            doc_count = len(chunks)
            document_frequency = Counter(
                term for terms in document_terms.values() for term in query_terms if term in terms
            )
            lexical = {}
            for chunk in chunks:
                terms = document_terms[chunk["id"]]
                lexical[chunk["id"]] = sum(
                    (1.0 + math.log((doc_count + 1) / (document_frequency[term] + 1)))
                    * (terms[term] / (terms[term] + 1.2))
                    for term in query_terms if terms[term]
                )
            vector_order = sorted(chunks, key=lambda chunk: similarities[chunk["id"]], reverse=True)
            lexical_order = sorted((chunk for chunk in chunks if lexical[chunk["id"]] > 0),
                                   key=lambda chunk: lexical[chunk["id"]], reverse=True)
            scores = {chunk["id"]: 0.65 / (10 + rank)
                      for rank, chunk in enumerate(vector_order, start=1)}
            for rank, chunk in enumerate(lexical_order, start=1):
                scores[chunk["id"]] += 0.35 / (10 + rank)

        ranked = sorted(chunks, key=lambda chunk: scores[chunk["id"]], reverse=True)[:top_k]
        return [
            {"chunk_id": chunk["id"], "source_id": chunk["source_id"],
             "source_name": chunk["source_name"], "source_kind": chunk["source_kind"],
             "source_uri": chunk["source_uri"], "chunk_index": chunk["chunk_index"],
             "text": chunk["text"], "score": round(scores[chunk["id"]], 6),
             "citation": f"{chunk['source_name']} (chunk {chunk['chunk_index'] + 1})"}
            for chunk in ranked
        ]
