import unittest

from app.schemas import AnalyzeRequest, AnalyzeResponse, COutput, RoadmapPreferences


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

    def test_analyze_request_does_not_dump_user_api_key(self) -> None:
        request = AnalyzeRequest(
            job_posting={
                "source_type": "text",
                "text": "백엔드 개발자. Docker 기반 배포 경험 필수.",
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
            openai_api_key="sk-test-secret",
        )
        self.assertEqual(request.openai_api_key, "sk-test-secret")
        self.assertNotIn("openai_api_key", request.model_dump())

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
            partial_skills=[],
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

    def test_c_output_accepts_partial_skills(self) -> None:
        payload = {
            "predicted_job": "백엔드 개발자",
            "fit_score": 55,
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
        result = COutput.model_validate(payload)
        self.assertEqual(result.partial_skills[0].skill, "AWS")
