import unittest

from app.services.text_extractor import clean_text, extract_from_text_source


class TextExtractorTest(unittest.TestCase):
    def test_clean_text_removes_duplicate_spaces(self) -> None:
        self.assertEqual(clean_text("  Python   SQL\n\nDocker  "), "Python SQL Docker")

    def test_extract_from_text_source_returns_clean_text(self) -> None:
        result = extract_from_text_source("  Spring Boot   API 개발  ")
        self.assertEqual(result, "Spring Boot API 개발")
