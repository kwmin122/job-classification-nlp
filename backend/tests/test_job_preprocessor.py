import unittest
from unittest.mock import Mock

from app.services.job_preprocessor import normalize_tech, preprocess_for_job_classifier


class JobPreprocessorTest(unittest.TestCase):
    def test_normalize_tech_converts_common_terms(self) -> None:
        text = normalize_tech("파이썬과 도커, spring boot, rest api 경험")
        self.assertIn("Python", text)
        self.assertIn("Docker", text)
        self.assertIn("SpringBoot", text)
        self.assertIn("RESTAPI", text)

    def test_preprocess_filters_stopwords_and_keeps_model_tokens(self) -> None:
        okt = Mock()
        okt.pos.return_value = [
            ("백엔드", "Noun"),
            ("개발", "Noun"),
            ("Docker", "Alpha"),
            ("배포", "Noun"),
            ("필수", "Noun"),
            ("경험", "Noun"),
        ]
        result = preprocess_for_job_classifier("백엔드 개발 Docker 배포 필수 경험", okt=okt)
        self.assertEqual(result, "백엔드 Docker 배포")
