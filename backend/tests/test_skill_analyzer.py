import unittest

from app.services.skill_analyzer import analyze_skill_gap


class SkillAnalyzerTest(unittest.TestCase):
    def test_detects_missing_skill_from_job_posting(self) -> None:
        result = analyze_skill_gap(
            job_text="백엔드 개발자. Docker 기반 배포 경험과 AWS 운영 경험 필수.",
            candidate_text="Spring Boot와 MySQL 기반 API를 개발했습니다.",
        )
        missing_names = [item.skill for item in result.missing_skills]
        self.assertIn("Docker", missing_names)
        self.assertIn("AWS", missing_names)

    def test_fit_score_reflects_owned_required_skills(self) -> None:
        result = analyze_skill_gap(
            job_text="백엔드 개발자. Docker와 Spring Boot 경험 필수.",
            candidate_text="Spring Boot 기반 API를 개발했습니다.",
        )
        self.assertEqual(result.fit_score, 55.0)

    def test_negated_candidate_skill_is_not_counted_as_owned(self) -> None:
        result = analyze_skill_gap(
            job_text="백엔드 개발자. Docker 기반 배포 경험과 AWS 운영 경험 필수.",
            candidate_text="Spring Boot 기반 API를 개발했습니다. Docker와 AWS 배포 경험은 아직 없습니다.",
        )
        owned_names = [item.skill for item in result.owned_skills]
        missing_names = [item.skill for item in result.missing_skills]

        self.assertNotIn("Docker", owned_names)
        self.assertNotIn("AWS", owned_names)
        self.assertIn("Docker", missing_names)
        self.assertIn("AWS", missing_names)
        self.assertTrue(all(item.gap_score > 90 for item in result.missing_skills))
