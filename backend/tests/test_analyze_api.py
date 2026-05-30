import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding_retriever import RetrieverInfo
from app.services.job_classifier import JobClassification
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
            "app.main.classify_job",
            return_value=JobClassification(
                predicted_job="백엔드 개발자",
                job_label="backend",
                job_probabilities={
                    "AI/ML 엔지니어": 0.01,
                    "백엔드 개발자": 0.95,
                    "데이터 분석가": 0.02,
                    "프론트엔드 개발자": 0.02,
                },
                classifier_source="ab_ensemble",
            ),
        ), patch(
            "app.main.run_c_part_analysis",
            return_value={
                "status": "success",
                "predicted_job": "백엔드 개발자",
                "fit_score": 55,
                "required_skills": [
                    {
                        "skill": "Docker",
                        "importance": "필수",
                        "source_sentence": "Docker 기반 배포 경험 필수.",
                    },
                    {
                        "skill": "AWS",
                        "importance": "우대",
                        "source_sentence": "AWS 배포 경험 우대.",
                    },
                    {
                        "skill": "Spring Boot",
                        "importance": "필수",
                        "source_sentence": "Spring Boot 개발 경험 필수.",
                    },
                ],
                "owned_skills": [
                    {
                        "skill": "Spring Boot",
                        "evidence": "Spring Boot API를 개발했습니다.",
                        "evidence_strength": "direct",
                    }
                ],
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
                "matched_skills": ["Spring Boot"],
                "skill_gaps": [
                    {
                        "skill": "Docker",
                        "gap_score": 85,
                        "gap_level": "높음",
                        "importance": "필수",
                        "evidence": "Docker 경험 문장이 확인되지 않음",
                    }
                ],
            },
        ) as c_mock, patch(
            "app.main.build_retriever",
            return_value=(
                StableRetriever(),
                RetrieverInfo(
                    retrieval_mode="bge_m3_fallback",
                    embedding_model="BAAI/bge-m3",
                    chunking_strategy="one_resource_row_per_chunk",
                ),
            ),
        ) as retriever_mock:
            response = client.post(
                "/analyze",
                json={
                    "job_posting": {
                        "source_type": "text",
                        "text": "백엔드 개발자. Docker 기반 배포 경험 필수. AWS 배포 경험 우대.",
                    },
                    "candidate_materials": [
                        {
                            "source_type": "text",
                            "label": "자소서",
                            "text": (
                                "Spring Boot API를 개발했습니다. "
                                "AWS EC2를 간단히 사용해 본 경험이 있습니다."
                            ),
                        }
                    ],
                    "roadmap_preferences": {
                        "duration_weeks": 4,
                        "difficulty": "입문",
                        "intensity": "보통",
                    },
                    "openai_api_key": " sk-test-request-key ",
                },
            )
        self.assertEqual(c_mock.call_args.kwargs["b_predicted_job"], "backend")
        self.assertEqual(retriever_mock.call_args.kwargs["api_key"], "sk-test-request-key")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["roadmap_preferences"]["duration_weeks"], 4)
        self.assertEqual(body["predicted_job"], "백엔드 개발자")
        self.assertEqual(body["job_label"], "backend")
        self.assertEqual(body["classifier_source"], "ab_ensemble")
        self.assertTrue(any(item["skill"] == "Docker" for item in body["missing_skills"]))
        self.assertEqual(body["partial_skills"][0]["skill"], "AWS")
        self.assertEqual(len(body["weekly_roadmap"]), 4)
        self.assertTrue(body["recommended_resources"])
        self.assertIn("Docker", body["report"])
        self.assertIn("AWS", body["report"])

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


class TestDetermineJdQuality(unittest.TestCase):
    def test_weak_when_no_structured_skills_and_few_required(self) -> None:
        from app.main import _determine_jd_quality
        self.assertEqual(_determine_jd_quality([], 0), "weak")
        self.assertEqual(_determine_jd_quality([], 2), "weak")

    def test_ok_when_structured_skills_present(self) -> None:
        from app.main import _determine_jd_quality
        self.assertEqual(_determine_jd_quality(["Python", "Go"], 0), "ok")

    def test_ok_when_required_count_3_or_more(self) -> None:
        from app.main import _determine_jd_quality
        self.assertEqual(_determine_jd_quality([], 3), "ok")
        self.assertEqual(_determine_jd_quality([], 5), "ok")
