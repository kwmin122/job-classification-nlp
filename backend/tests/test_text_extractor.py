import subprocess as _subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.text_extractor import (
    _decode_jobkorea_rsc,
    _extract_jobkorea_skills,
    _extract_jobkorea_workfield,
    clean_text,
    extract_file_bytes,
    extract_from_text_source,
    extract_text_input,
    extract_visible_text_from_html,
)


class TextExtractorTest(unittest.TestCase):
    def test_clean_text_removes_duplicate_spaces(self) -> None:
        self.assertEqual(clean_text("  Python   SQL\n\nDocker  "), "Python SQL Docker")

    def test_extract_from_text_source_returns_clean_text(self) -> None:
        result = extract_from_text_source("  Spring Boot   API 개발  ")
        self.assertEqual(result, "Spring Boot API 개발")

    def test_extract_text_input_returns_metadata(self) -> None:
        result = extract_text_input("  Docker   AWS  ")
        self.assertEqual(result.text, "Docker AWS")
        self.assertEqual(result.source_type, "text")
        self.assertEqual(result.extractor, "direct_text")

    def test_extract_txt_bytes_supports_cp949(self) -> None:
        result = extract_file_bytes(
            "백엔드 개발자 Docker 배포 경험".encode("cp949"),
            filename="resume.txt",
            content_type="text/plain",
        )
        self.assertEqual(result.source_type, "txt")
        self.assertIn("Docker", result.text)
        self.assertTrue(result.warnings)

    def test_extract_visible_text_from_html_ignores_navigation_and_script(self) -> None:
        html = """
        <html>
          <body>
            <nav>메뉴</nav>
            <main>
              <h1>백엔드 개발자 채용</h1>
              <p>Docker와 AWS 배포 경험이 필요합니다.</p>
            </main>
            <script>console.log("ignore")</script>
          </body>
        </html>
        """
        result = extract_visible_text_from_html(html)
        self.assertIn("백엔드 개발자 채용", result)
        self.assertIn("Docker와 AWS", result)
        self.assertNotIn("console", result)
        self.assertNotIn("메뉴", result)

    def test_extract_pdf_bytes_falls_back_to_ocr_when_pypdf_returns_empty(self) -> None:
        """PyPDF2와 pdftotext가 모두 빈 결과를 내면 OCR을 시도해야 한다."""
        from unittest.mock import patch
        from app.services.text_extractor import extract_pdf_bytes

        with (
            patch(
                "app.services.text_extractor._extract_pdf_with_pypdf",
                return_value=("", []),
            ),
            patch(
                "app.services.text_extractor._extract_pdf_with_pdftotext",
                return_value="",
            ),
            patch(
                "app.services.text_extractor._extract_pdf_with_ocr",
                return_value=("추출된 텍스트", ["스캔 PDF를 OCR로 처리했습니다."]),
            ),
        ):
            result = extract_pdf_bytes(b"fake-pdf")

        assert result.text == "추출된 텍스트"
        assert result.extractor == "tesseract-ocr"
        assert any("OCR" in w for w in result.warnings)

    def test_extract_pdf_with_ocr_returns_empty_on_import_error(self) -> None:
        """pdf2image 미설치 시 예외 없이 빈 문자열을 반환해야 한다."""
        import sys
        from unittest.mock import patch
        from app.services.text_extractor import _extract_pdf_with_ocr

        # sys.modules에 None을 넣으면 해당 모듈 import 시 ImportError 발생
        with patch.dict(sys.modules, {"pdf2image": None}):
            text, warnings = _extract_pdf_with_ocr(b"fake-pdf")

        assert text == ""
        assert warnings == []


class TestJobkoreaRscParsing(unittest.TestCase):
    """fixture HTML을 사용한 잡코리아 RSC 파싱 단위 테스트 (네트워크 의존 없음)."""

    FIXTURE_DIR = Path(__file__).parent / "fixtures"

    def _load(self, name: str) -> str:
        return (self.FIXTURE_DIR / name).read_text(encoding="utf-8", errors="replace")

    def test_skills_extracted_ai_posting(self) -> None:
        html = self._load("jobkorea_49244543.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertIn("Python", skills)
        self.assertIn("LLMOps", skills)
        self.assertIn("AI Agent", skills)
        self.assertIn("RPA", skills)

    def test_workfield_extracted_ai_posting(self) -> None:
        html = self._load("jobkorea_49244543.html")
        payload = _decode_jobkorea_rsc(html)
        title = _extract_jobkorea_workfield(payload)
        self.assertIsNotNone(title)
        self.assertIn("AI", title)  # must contain "AI" for 49244543 posting

    def test_skills_extracted_backend_nodejs(self) -> None:
        html = self._load("jobkorea_43134476.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertIn("Node.js", skills)
        self.assertIn("Go", skills)
        self.assertIn("NoSQL", skills)

    def test_skills_extracted_backend_java(self) -> None:
        html = self._load("jobkorea_48391099.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertIn("JAVA", skills)
        self.assertIn("Spring Boot", skills)

    def test_no_duplicate_skills(self) -> None:
        html = self._load("jobkorea_49244543.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertEqual(len(skills), len(set(skills)))

    def test_hh_posting_returns_empty_skills(self) -> None:
        """RSC 없는 HTML → 빈 skills 반환."""
        html_no_rsc = "<html><body><p>헤드헌팅 공고 본문</p></body></html>"
        payload = _decode_jobkorea_rsc(html_no_rsc)
        skills = _extract_jobkorea_skills(payload)
        self.assertEqual(skills, [])


class TestExtractWithPlaywright(unittest.TestCase):
    """_extract_with_playwright 단위 테스트 — subprocess mock, 네트워크 없음."""

    def _call(self, stdout: str, returncode: int = 0, side_effect=None) -> str:
        from app.services.text_extractor import _extract_with_playwright

        mock_result = MagicMock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = ""
        with patch("app.services.text_extractor.subprocess.run") as mock_run:
            if side_effect:
                mock_run.side_effect = side_effect
            else:
                mock_run.return_value = mock_result
            return _extract_with_playwright("https://example.com")

    def test_returns_text_on_success(self) -> None:
        result = self._call("Python LLMOps LangChain RAG 개발 경험")
        self.assertIn("Python", result)
        self.assertIn("LLMOps", result)

    def test_returns_empty_on_nonzero_exit(self) -> None:
        result = self._call("", returncode=1)
        self.assertEqual(result, "")

    def test_returns_empty_on_timeout(self) -> None:
        result = self._call("", side_effect=_subprocess.TimeoutExpired("node", 30))
        self.assertEqual(result, "")

    def test_returns_empty_on_file_not_found(self) -> None:
        result = self._call("", side_effect=FileNotFoundError("node not found"))
        self.assertEqual(result, "")

    def test_cleans_whitespace(self) -> None:
        result = self._call("AI 엔지니어\n\n  담당업무  \n생성형 AI")
        self.assertNotIn("  ", result)
