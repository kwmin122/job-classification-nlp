from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding_retriever import RetrieverInfo
from app.services.resource_loader import load_resources


def recommend_payload() -> dict:
    return {
        "predicted_job": "백엔드 개발자",
        "fit_score": 55,
        "matched_skills": ["Spring Boot"],
        "skill_gaps": [
            {
                "skill": "Docker",
                "gap_score": 90,
                "gap_level": "높음",
                "importance": "필수",
                "evidence": "채용공고에는 Docker 역량이 요구되지만 지원자 자료에는 충분한 근거가 없음",
            }
        ],
    }


class RecommendApiTest(unittest.TestCase):
    def test_recommend_response_exposes_retrieval_metadata(self) -> None:
        class StableRetriever:
            def search(self, query: str, limit: int = 8):
                from app.services.resource_loader import load_resources

                return [(resource, 0.9) for resource in load_resources()[:limit]]

        client = TestClient(app)

        with patch(
            "app.main.build_retriever",
            return_value=(
                StableRetriever(),
                RetrieverInfo(
                    retrieval_mode="bge_m3_fallback",
                    embedding_model="BAAI/bge-m3",
                    chunking_strategy="one_resource_row_per_chunk",
                ),
            ),
        ):
            response = client.post("/recommend", json=recommend_payload())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_mode"], "bge_m3_fallback")
        self.assertEqual(body["embedding_model"], "BAAI/bge-m3")
        self.assertEqual(body["chunking_strategy"], "one_resource_row_per_chunk")

    def test_recommend_falls_back_when_embedding_search_fails(self) -> None:
        class BrokenRetriever:
            def search(self, query: str, limit: int = 8):
                raise RuntimeError("embedding API failed")

        client = TestClient(app)

        with patch(
            "app.main.build_retriever",
            return_value=(
                BrokenRetriever(),
                RetrieverInfo(
                    retrieval_mode="embedding",
                    embedding_model="text-embedding-3-small",
                    chunking_strategy="one_resource_row_per_chunk",
                ),
            ),
        ):
            response = client.post("/recommend", json=recommend_payload())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_mode"], "tfidf_last_resort")
        self.assertEqual(body["embedding_model"], "none")

    def test_recommend_prefers_same_job_group_for_same_skill(self) -> None:
        previous_key = os.environ.pop("OPENAI_API_KEY", None)
        payload = {
            "predicted_job": "백엔드 개발자",
            "fit_score": 25,
            "matched_skills": ["Spring Boot"],
            "skill_gaps": [
                {
                    "skill": "AWS",
                    "gap_score": 80,
                    "gap_level": "높음",
                    "importance": "필수",
                    "evidence": "채용공고에는 AWS 역량이 요구되지만 지원자 자료에는 명확히 나타나지 않음",
                }
            ],
        }

        try:
            client = TestClient(app)
            class AwsRetriever:
                def search(self, query: str, limit: int = 8):
                    resources = [
                        resource for resource in load_resources() if resource.skill == "AWS"
                    ]
                    return [(resource, 0.9) for resource in resources[:limit]]

            with patch(
                "app.main.build_retriever",
                return_value=(
                    AwsRetriever(),
                    RetrieverInfo(
                        retrieval_mode="bge_m3_fallback",
                        embedding_model="BAAI/bge-m3",
                        chunking_strategy="one_resource_row_per_chunk",
                    ),
                ),
            ):
                response = client.post("/recommend", json=payload)
        finally:
            if previous_key is not None:
                os.environ["OPENAI_API_KEY"] = previous_key

        self.assertEqual(response.status_code, 200)
        first = response.json()["skill_recommendations"][0]["recommendations"][0]
        self.assertEqual(first["resource"]["job_group"], "백엔드 개발자")


if __name__ == "__main__":
    unittest.main()
