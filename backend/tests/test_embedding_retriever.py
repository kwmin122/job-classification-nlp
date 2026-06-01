from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.schemas import Resource
from app.services.embedding_retriever import (
    DEFAULT_LOCAL_EMBEDDING_MODEL,
    EmbeddingRetriever,
    RetrieverInfo,
    build_retriever,
)
from app.services.retriever import TfidfRetriever


def resource(resource_id: str, skill: str, description: str) -> Resource:
    return Resource(
        id=resource_id,
        job_group="백엔드 개발자",
        skill=skill,
        sub_skill=skill,
        title=f"{skill} 학습 자료",
        description=description,
        url="https://example.com",
        type="공식문서",
        level="beginner",
        language="한국어",
        free_or_paid="무료",
        estimated_time="2시간",
        reliability=5,
        reason=f"{skill} 보완에 적합",
    )


class EmbeddingRetrieverTest(unittest.TestCase):
    def test_embedding_search_returns_highest_cosine_match(self) -> None:
        resources = [
            resource("BE001", "Docker", "컨테이너 배포 학습"),
            resource("BE002", "AWS", "클라우드 인프라 학습"),
        ]

        vectors = {
            "Docker": [1.0, 0.0],
            "AWS": [0.0, 1.0],
            "query": [0.9, 0.1],
        }

        def embedder(texts: list[str]) -> list[list[float]]:
            result: list[list[float]] = []
            for text in texts:
                if "Docker" in text:
                    result.append(vectors["Docker"])
                elif "AWS" in text:
                    result.append(vectors["AWS"])
                else:
                    result.append(vectors["query"])
            return result

        with tempfile.TemporaryDirectory() as temp_dir:
            retriever = EmbeddingRetriever(
                resources=resources,
                embedder=embedder,
                cache_dir=Path(temp_dir),
                model="test-embedding",
            )

            result = retriever.search("컨테이너 기반 배포 경험", limit=1)

        self.assertEqual(result[0][0].id, "BE001")
        self.assertGreater(result[0][1], 0.9)

    def test_build_retriever_uses_local_sentence_transformer_fallback_without_api_key(self) -> None:
        resources = [resource("BE001", "Docker", "컨테이너 배포 학습")]

        def embedder(texts: list[str]) -> list[list[float]]:
            return [[1.0, 0.0] for _ in texts]

        with tempfile.TemporaryDirectory() as temp_dir:
            retriever, info = build_retriever(
                resources,
                api_key="",
                local_embedder=embedder,
                cache_dir=Path(temp_dir),
            )

        self.assertIsInstance(retriever, EmbeddingRetriever)
        self.assertEqual(
            info,
            RetrieverInfo(
                retrieval_mode="local_sentence_transformer_fallback",
                embedding_model=DEFAULT_LOCAL_EMBEDDING_MODEL,
                chunking_strategy="one_resource_row_per_chunk",
            ),
        )

    def test_build_retriever_uses_tfidf_only_when_local_fallback_fails(self) -> None:
        resources = [resource("BE001", "Docker", "컨테이너 배포 학습")]

        def broken_embedder(texts: list[str]) -> list[list[float]]:
            raise RuntimeError("local model unavailable")

        with tempfile.TemporaryDirectory() as temp_dir:
            retriever, info = build_retriever(
                resources,
                api_key="",
                local_embedder=broken_embedder,
                cache_dir=Path(temp_dir),
            )

        self.assertIsInstance(retriever, TfidfRetriever)
        self.assertEqual(
            info,
            RetrieverInfo(
                retrieval_mode="tfidf_last_resort",
                embedding_model="none",
                chunking_strategy="one_resource_row_per_chunk",
            ),
        )


if __name__ == "__main__":
    unittest.main()
