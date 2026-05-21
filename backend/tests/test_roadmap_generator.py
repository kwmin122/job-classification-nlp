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
