from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding_retriever import RetrieverInfo
from app.services.resource_loader import load_resources


class StableRetriever:
    def search(self, query: str, limit: int = 8):
        resources = load_resources()
        scored = [
            (resource, 0.95 if resource.skill in query else 0.1)
            for resource in resources
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]


class PartialRecommendationTest(unittest.TestCase):
    def test_gap_targets_come_before_partial_targets(self) -> None:
        payload = {
            "predicted_job": "백엔드 개발자",
            "fit_score": 45,
            "matched_skills": ["Spring Boot"],
            "partial_skills": [
                {
                    "skill": "AWS",
                    "evidence": "AWS EC2를 간단히 사용해 본 경험이 있습니다.",
                    "evidence_strength": "contextual",
                    "gap_score": 55,
                    "gap_level": "중간",
                    "importance": "우대",
                    "note": "충족 임계값 미달 - 학습 보완 필요",
                }
            ],
            "skill_gaps": [
                {
                    "skill": "Docker",
                    "gap_score": 85,
                    "gap_level": "높음",
                    "importance": "필수",
                    "evidence": "Docker 경험 문장이 확인되지 않음",
                }
            ],
        }
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
            response = TestClient(app).post("/recommend", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["skill_recommendations"][0]["target_type"], "gap")
        self.assertEqual(body["skill_recommendations"][0]["skill"], "Docker")
        self.assertEqual(body["skill_recommendations"][1]["target_type"], "partial")
        self.assertEqual(body["skill_recommendations"][1]["skill"], "AWS")
        self.assertEqual(body["roadmap"][0]["skill"], "Docker")

    def test_owned_skills_are_not_recommended_without_gap_or_partial(self) -> None:
        payload = {
            "predicted_job": "백엔드 개발자",
            "fit_score": 100,
            "matched_skills": ["Spring Boot", "Docker"],
            "partial_skills": [],
            "skill_gaps": [],
        }
        response = TestClient(app).post("/recommend", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["skill_recommendations"], [])


if __name__ == "__main__":
    unittest.main()
