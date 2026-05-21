import unittest

from app.schemas import Resource
from app.services.scorer import difficulty_match, score_resource


def resource(level: str) -> Resource:
    return Resource(
        id="R1",
        job_group="백엔드 개발자",
        skill="Docker",
        sub_skill="컨테이너",
        title="Docker 입문",
        description="Docker 기본",
        url="https://example.com",
        type="공식문서",
        level=level,
        language="한국어",
        free_or_paid="무료",
        estimated_time="3시간",
        reliability=5,
        reason="Docker 보완",
    )


class ScorerTest(unittest.TestCase):
    def test_difficulty_match_prefers_beginner_for_intro_user(self) -> None:
        self.assertEqual(difficulty_match("입문", resource("beginner")), 1.0)
        self.assertEqual(difficulty_match("입문", resource("advanced")), 0.0)

    def test_score_resource_includes_difficulty(self) -> None:
        beginner = score_resource(resource("beginner"), 0.8, "Docker", "백엔드 개발자", "입문")
        advanced = score_resource(resource("advanced"), 0.8, "Docker", "백엔드 개발자", "입문")
        self.assertGreater(beginner.recommend_score, advanced.recommend_score)
