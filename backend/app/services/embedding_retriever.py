from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

import numpy as np

from app.schemas import Resource
from app.services.resource_loader import DATA_DIR, resource_search_text
from app.services.retriever import TfidfRetriever

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_LOCAL_EMBEDDING_MODEL = "BAAI/bge-m3"
CHUNKING_STRATEGY = "one_resource_row_per_chunk"
CACHE_DIR = DATA_DIR.parent / "cache"
EMBEDDINGS_FILENAME = "resource_embeddings.npz"
META_FILENAME = "resource_index_meta.json"

Embedder = Callable[[list[str]], list[list[float]]]


class Retriever(Protocol):
    def search(self, query: str, limit: int = 8) -> list[tuple[Resource, float]]:
        ...


@dataclass(frozen=True)
class RetrieverInfo:
    retrieval_mode: str
    embedding_model: str
    chunking_strategy: str


def build_retriever(
    resources: list[Resource],
    *,
    api_key: str | None = None,
    model: str = DEFAULT_EMBEDDING_MODEL,
    local_model: str = DEFAULT_LOCAL_EMBEDDING_MODEL,
    local_embedder: Embedder | None = None,
    cache_dir: Path = CACHE_DIR,
) -> tuple[Retriever, RetrieverInfo]:
    key = os.getenv("OPENAI_API_KEY") if api_key is None else api_key
    if key:
        try:
            return (
                EmbeddingRetriever(
                    resources=resources,
                    api_key=key,
                    model=model,
                    cache_dir=cache_dir,
                ),
                RetrieverInfo(
                    retrieval_mode="embedding",
                    embedding_model=model,
                    chunking_strategy=CHUNKING_STRATEGY,
                ),
            )
        except Exception:
            pass

    try:
        return (
            EmbeddingRetriever(
                resources=resources,
                model=local_model,
                embedder=local_embedder or BgeM3Embedder(model=local_model),
                cache_dir=cache_dir,
            ),
            RetrieverInfo(
                retrieval_mode="bge_m3_fallback",
                embedding_model=local_model,
                chunking_strategy=CHUNKING_STRATEGY,
            ),
        )
    except Exception:
        return (
            TfidfRetriever(resources),
            RetrieverInfo(
                retrieval_mode="tfidf_last_resort",
                embedding_model="none",
                chunking_strategy=CHUNKING_STRATEGY,
            ),
        )


class EmbeddingRetriever:
    def __init__(
        self,
        resources: list[Resource],
        *,
        model: str = DEFAULT_EMBEDDING_MODEL,
        api_key: str | None = None,
        embedder: Embedder | None = None,
        cache_dir: Path = CACHE_DIR,
    ) -> None:
        self.resources = resources
        self.model = model
        self.cache_dir = cache_dir
        self.embedder = embedder or OpenAIEmbedder(model=model, api_key=api_key)
        self.documents = [resource_search_text(resource) for resource in resources]
        self.resource_fingerprint = _resource_fingerprint(resources, self.documents)
        self.embedding_matrix = self._load_or_build_embeddings()

    def search(self, query: str, limit: int = 8) -> list[tuple[Resource, float]]:
        if not self.resources:
            return []

        query_vector = _normalize_matrix(np.array(self.embedder([query]), dtype=np.float32))[0]
        similarities = self.embedding_matrix @ query_vector
        scored = [
            (resource, float(similarity))
            for resource, similarity in zip(self.resources, similarities, strict=True)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    def _load_or_build_embeddings(self) -> np.ndarray:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        embeddings_path = self.cache_dir / EMBEDDINGS_FILENAME
        meta_path = self.cache_dir / META_FILENAME

        if embeddings_path.exists() and meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as file:
                meta = json.load(file)
            if self._is_cache_valid(meta):
                matrix = np.load(embeddings_path)["embeddings"].astype(np.float32)
                return _normalize_matrix(matrix)

        matrix = _normalize_matrix(np.array(self.embedder(self.documents), dtype=np.float32))
        np.savez_compressed(embeddings_path, embeddings=matrix)
        with meta_path.open("w", encoding="utf-8") as file:
            json.dump(self._cache_meta(matrix), file, ensure_ascii=False, indent=2)
        return matrix

    def _is_cache_valid(self, meta: dict) -> bool:
        return (
            meta.get("model") == self.model
            and meta.get("chunking_strategy") == CHUNKING_STRATEGY
            and meta.get("resource_fingerprint") == self.resource_fingerprint
            and meta.get("resource_ids") == [resource.id for resource in self.resources]
        )

    def _cache_meta(self, matrix: np.ndarray) -> dict:
        return {
            "model": self.model,
            "chunking_strategy": CHUNKING_STRATEGY,
            "resource_fingerprint": self.resource_fingerprint,
            "resource_ids": [resource.id for resource in self.resources],
            "dimension": int(matrix.shape[1]) if matrix.ndim == 2 and matrix.size else 0,
        }


class OpenAIEmbedder:
    def __init__(self, *, model: str, api_key: str | None = None) -> None:
        self.model = model
        self.api_key = api_key

    def __call__(self, texts: list[str]) -> list[list[float]]:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class BgeM3Embedder:
    def __init__(self, *, model: str = DEFAULT_LOCAL_EMBEDDING_MODEL) -> None:
        self.model = model
        self.encoder = None

    def __call__(self, texts: list[str]) -> list[list[float]]:
        if self.encoder is None:
            from sentence_transformers import SentenceTransformer

            self.encoder = SentenceTransformer(self.model)
        embeddings = self.encoder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
        )
        return embeddings.tolist()


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 2:
        raise ValueError("embedding matrix must be two-dimensional")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return matrix / norms


def _resource_fingerprint(resources: list[Resource], documents: list[str]) -> str:
    digest = hashlib.sha256()
    for resource, document in zip(resources, documents, strict=True):
        digest.update(resource.id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(document.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
