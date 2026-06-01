import unittest

from app.services.job_label_mapping import LABEL_ORDER, LABEL_TO_JOB, to_job_name


class JobLabelMappingTest(unittest.TestCase):
    def test_label_order_matches_ab_output(self) -> None:
        self.assertEqual(LABEL_ORDER, ["ai", "backend", "data_analyst", "frontend"])

    def test_to_job_name_returns_korean_display_name(self) -> None:
        self.assertEqual(to_job_name("ai"), "AI/ML 엔지니어")
        self.assertEqual(to_job_name("backend"), "백엔드 개발자")
        self.assertEqual(to_job_name("data_analyst"), "데이터 분석가")
        self.assertEqual(to_job_name("frontend"), "프론트엔드 개발자")

    def test_all_labels_have_display_names(self) -> None:
        self.assertEqual(set(LABEL_ORDER), set(LABEL_TO_JOB))
