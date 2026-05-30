from __future__ import annotations

import unittest

from app.schemas import MissingSkill, PartialSkill, RoadmapPreferences, WeeklyRoadmapItem
from app.services.report_generator import generate_product_report


class TestGenerateProductReport(unittest.TestCase):
    def _prefs(self) -> RoadmapPreferences:
        return RoadmapPreferences(duration_weeks=4, difficulty="실무", intensity="보통")

    def test_no_noise_text_in_report(self) -> None:
        """evidence 원문(접수기간/복지/주소)이 리포트에 포함되지 않는다."""
        missing = [MissingSkill(skill="LLMOps", gap_score=70, gap_level="높음", importance="필수",
                                evidence="공고 요구: LLMOps / 접수기간: ~2024-12-31 복지: 4대보험")]
        report = generate_product_report(
            predicted_job="AI/ML 엔지니어", fit_score=65,
            missing_skills=missing, partial_skills=[],
            weekly_roadmap=[], preferences=self._prefs(),
        )
        self.assertNotIn("접수기간", report)
        self.assertNotIn("복지", report)

    def test_weak_jd_no_fit_assertion(self) -> None:
        """jd_quality=weak이면 경고 문구가 있고 gap 단정 표현이 없다."""
        report = generate_product_report(
            predicted_job="미분류", fit_score=77,
            missing_skills=[], partial_skills=[],
            weekly_roadmap=[], preferences=self._prefs(),
            jd_quality="weak",
        )
        self.assertIn("명확한 기술 요구를 찾지 못했습니다", report)
        self.assertNotIn("77점", report)

    def test_structure_has_all_sections(self) -> None:
        """정상 리포트에 ①직무 ②카운트 ③보완 ④로드맵 섹션이 있다."""
        missing = [MissingSkill(skill="Go", gap_score=80, gap_level="높음", importance="필수", evidence="")]
        roadmap = [WeeklyRoadmapItem(week=1, goal="Go — 기초 개념", skills=["Go"], recommended_titles=[], practice="실습")]
        report = generate_product_report(
            predicted_job="백엔드 개발자", fit_score=60,
            missing_skills=missing, partial_skills=[],
            weekly_roadmap=roadmap, preferences=self._prefs(),
            owned_skills_count=2,
        )
        self.assertIn("역량 충족 현황", report)
        self.assertIn("최우선 보완 역량", report)
        self.assertIn("Go", report)
        self.assertIn("로드맵", report)

    def test_product_report_includes_partial_skills(self) -> None:
        """부족/보완 역량이 역량 충족 현황 카운트에 반영된다."""
        report = generate_product_report(
            predicted_job="백엔드 개발자",
            fit_score=55,
            missing_skills=[
                MissingSkill(
                    skill="Docker",
                    gap_score=85,
                    gap_level="높음",
                    importance="필수",
                    evidence="Docker 경험 문장이 확인되지 않음",
                )
            ],
            partial_skills=[
                PartialSkill(
                    skill="AWS",
                    evidence="AWS EC2를 간단히 사용해 본 경험이 있습니다.",
                    evidence_strength="contextual",
                    gap_score=55,
                    gap_level="중간",
                    importance="우대",
                    note="충족 임계값 미달 - 학습 보완 필요",
                )
            ],
            weekly_roadmap=[
                WeeklyRoadmapItem(
                    week=1,
                    goal="Docker 학습 및 실습",
                    skills=["Docker"],
                    recommended_titles=["Docker 공식 문서"],
                    practice="Docker를 적용한 작은 결과물을 만들고 정리하기",
                )
            ],
            preferences=RoadmapPreferences(duration_weeks=4, difficulty="입문", intensity="보통"),
        )

        self.assertIn("Docker", report)
        self.assertIn("보완 필요 1개", report)
        self.assertIn("역량 충족 현황", report)


if __name__ == "__main__":
    unittest.main()
