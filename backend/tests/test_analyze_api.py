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
            (resource, 0.9 if resource.skill in query else 0.1)
            for resource in resources
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]


class AnalyzeApiTest(unittest.TestCase):
    def test_analyze_returns_user_centered_result(self) -> None:
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
            response = client.post(
                "/analyze",
                json={
                    "job_posting": {
                        "source_type": "text",
                        "text": "백엔드 개발자. Docker 기반 배포 경험 필수.",
                    },
                    "candidate_materials": [
                        {
                            "source_type": "text",
                            "label": "자소서",
                            "text": "Spring Boot API를 개발했습니다.",
                        }
                    ],
                    "roadmap_preferences": {
                        "duration_weeks": 4,
                        "difficulty": "입문",
                        "intensity": "보통",
                    },
                },
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["roadmap_preferences"]["duration_weeks"], 4)
        self.assertEqual(body["predicted_job"], "백엔드 개발자")
        self.assertTrue(any(item["skill"] == "Docker" for item in body["missing_skills"]))
        self.assertEqual(len(body["weekly_roadmap"]), 4)
        self.assertTrue(body["recommended_resources"])
        self.assertIn("Docker", body["report"])

    def test_analyze_rejects_short_candidate_text(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/analyze",
            json={
                "job_posting": {
                    "source_type": "text",
                    "text": "백엔드 개발자. Docker 기반 배포 경험 필수.",
                },
                "candidate_materials": [
                    {
                        "source_type": "text",
                        "label": "자소서",
                        "text": "짧음",
                    }
                ],
                "roadmap_preferences": {
                    "duration_weeks": 4,
                    "difficulty": "입문",
                    "intensity": "보통",
                },
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("candidate", response.json()["detail"])
