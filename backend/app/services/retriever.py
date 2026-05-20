from __future__ import annotations

import math
import re
from collections import Counter

from app.schemas import Resource
from app.services.resource_loader import resource_search_text

TOKEN_RE = re.compile(r"[a-zA-Z0-9+#./-]+|[가-힣]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class TfidfRetriever:
    def __init__(self, resources: list[Resource]):
        self.resources = resources
        self.documents = [resource_search_text(resource) for resource in resources]
        self.doc_tokens = [tokenize(document) for document in self.documents]
        self.idf = self._build_idf()
        self.doc_vectors = [self._vectorize_tokens(tokens) for tokens in self.doc_tokens]

    def _build_idf(self) -> dict[str, float]:
        document_count = len(self.doc_tokens)
        document_frequency: Counter[str] = Counter()
        for tokens in self.doc_tokens:
            document_frequency.update(set(tokens))

        return {
            token: math.log((1 + document_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

    def _vectorize_tokens(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}

        counts = Counter(tokens)
        total = len(tokens)
        return {
            token: (count / total) * self.idf.get(token, 1.0)
            for token, count in counts.items()
        }

    def similarity(self, query: str, resource: Resource) -> float:
        try:
            index = self.resources.index(resource)
        except ValueError:
            return 0.0
        return self._cosine(self._vectorize_tokens(tokenize(query)), self.doc_vectors[index])

    def search(self, query: str, limit: int = 8) -> list[tuple[Resource, float]]:
        query_vector = self._vectorize_tokens(tokenize(query))
        scored = [
            (resource, self._cosine(query_vector, doc_vector))
            for resource, doc_vector in zip(self.resources, self.doc_vectors, strict=True)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0

        shared = set(a) & set(b)
        numerator = sum(a[token] * b[token] for token in shared)
        a_norm = math.sqrt(sum(value * value for value in a.values()))
        b_norm = math.sqrt(sum(value * value for value in b.values()))
        if a_norm == 0 or b_norm == 0:
            return 0.0
        return numerator / (a_norm * b_norm)

