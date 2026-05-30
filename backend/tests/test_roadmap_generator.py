import unittest

from app.schemas import RoadmapPreferences
from app.services.roadmap_generator import distribute_weeks


class RoadmapGeneratorTest(unittest.TestCase):
    def test_distribute_weeks_uses_selected_duration(self) -> None:
        weeks = distribute_weeks(
            ["Docker", "AWS"],
            RoadmapPreferences(duration_weeks=4, difficulty="입문", intensity="보통"),
        )
        self.assertEqual(len(weeks), 4)
        self.assertEqual(weeks[0]["week"], 1)
        self.assertIn("Docker", weeks[0]["skills"])


class TestDistributeWeeks(unittest.TestCase):
    """distribute_weeks 버그 수정 + PHASES 기반 다양성 검증."""

    def _prefs(self, weeks: int) -> object:
        # RoadmapPreferences 대신 간단한 mock 또는 실제 객체 사용
        from app.schemas import RoadmapPreferences
        return RoadmapPreferences(duration_weeks=weeks, difficulty="실무", intensity="보통")

    def test_single_skill_4weeks_goals_are_distinct(self) -> None:
        result = distribute_weeks(["Python"], self._prefs(4))
        self.assertEqual(len(result), 4)
        goals = [r["goal"] for r in result]
        self.assertEqual(len(set(goals)), 4, f"goals must all differ, got {goals}")

    def test_single_skill_4weeks_practices_are_distinct(self) -> None:
        result = distribute_weeks(["Docker"], self._prefs(4))
        practices = [r["practice"] for r in result]
        self.assertEqual(len(set(practices)), 4, f"practices must all differ, got {practices}")

    def test_5skills_4weeks_uses_top_4(self) -> None:
        skills = ["Python", "Docker", "React", "Go", "NoSQL"]
        result = distribute_weeks(skills, self._prefs(4))
        self.assertEqual(len(result), 4)
        covered = {r["skills"][0] for r in result}
        self.assertEqual(len(covered), 4)

    def test_2skills_4weeks_each_gets_2weeks(self) -> None:
        result = distribute_weeks(["Python", "Docker"], self._prefs(4))
        self.assertEqual(len(result), 4)
        python_weeks = sum(1 for r in result if "Python" in r["skills"])
        docker_weeks = sum(1 for r in result if "Docker" in r["skills"])
        self.assertEqual(python_weeks, 2)
        self.assertEqual(docker_weeks, 2)

    def test_empty_skills_returns_empty(self) -> None:
        result = distribute_weeks([], self._prefs(4))
        self.assertEqual(result, [])

    def test_weeks_sequential(self) -> None:
        result = distribute_weeks(["Python", "Go"], self._prefs(4))
        weeks = [r["week"] for r in result]
        self.assertEqual(weeks, list(range(1, 5)))
