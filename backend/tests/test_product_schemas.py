import unittest

from app.schemas import AnalyzeRequest, AnalyzeResponse, RoadmapPreferences


class ProductSchemaTest(unittest.TestCase):
    def test_analyze_request_accepts_user_inputs_and_preferences(self) -> None:
        request = AnalyzeRequest(
            job_posting={
                "source_type": "url",
                "url": "https://example.com/job",
                "text": "",
            },
            candidate_materials=[
                {
                    "source_type": "text",
                    "label": "자소서",
                    "text": "Spring Boot API 개발 경험이 있습니다.",
                }
            ],
            roadmap_preferences={
                "duration_weeks": 4,
                "difficulty": "입문",
                "intensity": "보통",
            },
        )
        self.assertEqual(request.roadmap_preferences.duration_weeks, 4)
        self.assertEqual(request.candidate_materials[0].label, "자소서")

    def test_roadmap_preferences_rejects_invalid_duration(self) -> None:
        with self.assertRaises(ValueError):
            RoadmapPreferences(duration_weeks=3, difficulty="입문", intensity="보통")

    def test_analyze_response_contains_product_outputs(self) -> None:
        response = AnalyzeResponse(
            predicted_job="백엔드 개발자",
            fit_score=75,
            roadmap_preferences={
                "duration_weeks": 4,
                "difficulty": "입문",
                "intensity": "보통",
            },
            required_skills=[],
            owned_skills=[],
            missing_skills=[],
            recommended_resources=[],
            weekly_roadmap=[],
            report="분석 리포트",
            scoring_formula="formula",
            rag_scope_note="curated db",
            retrieval_mode="bge_m3_fallback",
            embedding_model="BAAI/bge-m3",
            chunking_strategy="one resource row per chunk",
        )
        self.assertEqual(response.report, "분석 리포트")
