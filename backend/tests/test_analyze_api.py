import unittest

from fastapi.testclient import TestClient

from app.main import app


class AnalyzeApiTest(unittest.TestCase):
    def test_analyze_returns_user_centered_result(self) -> None:
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
