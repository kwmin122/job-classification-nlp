from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class TextExtractionError(ValueError):
    pass


@dataclass(frozen=True)
class TextExtractionResult:
    text: str
    source_type: str
    extractor: str
    warnings: list[str]
    structured_skills: list[str] = field(default_factory=list)
    job_title: str | None = None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_from_text_source(value: str) -> str:
    return clean_text(value)


def extract_text_input(value: str) -> TextExtractionResult:
    text = clean_text(value)
    if not text:
        raise TextExtractionError("text is empty")
    return TextExtractionResult(
        text=text,
        source_type="text",
        extractor="direct_text",
        warnings=[],
    )


def extract_file_bytes(
    content: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> TextExtractionResult:
    if not content:
        raise TextExtractionError("file is empty")

    lowered_name = (filename or "").lower()
    lowered_type = (content_type or "").lower()
    if lowered_name.endswith(".pdf") or lowered_type == "application/pdf":
        return extract_pdf_bytes(content)
    if lowered_name.endswith(".txt") or lowered_type.startswith("text/"):
        return extract_txt_bytes(content)
    raise TextExtractionError("only PDF and TXT files are supported")


def extract_pdf_bytes(content: bytes) -> TextExtractionResult:
    warnings: list[str] = []
    extractor = "pdf_text_extractor"

    # Stage 1: PyPDF2
    try:
        text, pypdf_warnings = _extract_pdf_with_pypdf(content)
        warnings.extend(pypdf_warnings)
    except TextExtractionError:
        text = ""
        warnings.append("PyPDF2 추출 실패 후 pdftotext fallback을 사용했습니다.")

    # Stage 2: pdftotext (시스템 커맨드)
    if not text:
        text = _extract_pdf_with_pdftotext(content)
        if text and not any("pdftotext" in w for w in warnings):
            warnings.append("PyPDF2 결과가 비어 있어 pdftotext fallback을 사용했습니다.")

    # Stage 3: OCR (스캔 PDF)
    if not text:
        text, ocr_warnings = _extract_pdf_with_ocr(content)
        if text:
            extractor = "tesseract-ocr"
            warnings.extend(ocr_warnings)

    if not text:
        raise TextExtractionError(
            "PDF에서 텍스트를 추출하지 못했습니다. "
            "스캔 PDF라면 직접 붙여넣어 주세요."
        )
    return TextExtractionResult(
        text=text,
        source_type="pdf",
        extractor=extractor,
        warnings=warnings,
    )


def _extract_pdf_with_pypdf(content: bytes) -> tuple[str, list[str]]:
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(BytesIO(content))
        page_texts = [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:  # pragma: no cover - PyPDF2 has broad parser exceptions
        raise TextExtractionError("PyPDF2 PDF text extraction failed") from exc

    warnings: list[str] = []
    empty_pages = sum(1 for page_text in page_texts if not page_text.strip())
    if empty_pages:
        warnings.append(f"{empty_pages}개 페이지에서 텍스트를 찾지 못했습니다.")
    return clean_text("\n".join(page_texts)), warnings


def _extract_pdf_with_pdftotext(content: bytes) -> str:
    executable = shutil.which("pdftotext")
    if executable is None:
        return ""

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / "input.pdf"
        output_path = Path(tmp_dir) / "output.txt"
        input_path.write_bytes(content)
        completed = subprocess.run(
            [executable, "-layout", str(input_path), str(output_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if completed.returncode != 0 or not output_path.exists():
            return ""
        return clean_text(output_path.read_text(encoding="utf-8", errors="replace"))


def extract_txt_bytes(content: bytes) -> TextExtractionResult:
    warnings: list[str] = []
    text: str | None = None
    for encoding in ("utf-8", "cp949"):
        try:
            text = content.decode(encoding)
            if encoding != "utf-8":
                warnings.append("UTF-8 디코딩 실패 후 CP949로 읽었습니다.")
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise TextExtractionError("TXT 인코딩을 해석하지 못했습니다.")

    cleaned = clean_text(text)
    if not cleaned:
        raise TextExtractionError("TXT 파일에 분석할 텍스트가 없습니다.")
    return TextExtractionResult(
        text=cleaned,
        source_type="txt",
        extractor="txt_decoder",
        warnings=warnings,
    )


def _decode_jobkorea_rsc(html: str) -> str:
    """self.__next_f.push([N, "...JSON..."]) 청크들을 합쳐 RSC 페이로드 반환."""
    chunks = re.findall(r'self\.__next_f\.push\(\[\d+,("(?:[^"\\]|\\.)*")\]\)', html)
    out = []
    for c in chunks:
        try:
            out.append(json.loads(c))
        except Exception:
            pass
    return "".join(out)


def _extract_jobkorea_skills(payload: str) -> list[str]:
    """RSC 페이로드에서 HARD_SKILL name 목록 추출 (순서 유지, 중복 제거)."""
    pairs = re.findall(
        r'\{"name":"([^"]+)","rank":\d+,"manualInput":(?:true|false),"skillTypeCode":"HARD_SKILL"\}',
        payload,
    )
    seen: set[str] = set()
    result: list[str] = []
    for name in pairs:
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _extract_jobkorea_workfield(payload: str) -> str | None:
    """RSC 페이로드에서 첫 번째 workField(직무명) 추출."""
    m = re.search(r'"workFields":\["([^"]+)"', payload)
    return m.group(1) if m else None


def _extract_jobkorea_description_url(payload: str) -> str | None:
    """RSC 페이로드에서 job-hub S3 공고 본문 HTML pre-signed URL 추출.

    잡코리아는 스킬 등록란이 비어있는 공고의 상세 본문을 S3 pre-signed URL로 제공.
    URL은 페이지 로드 시점부터 900초(15분) 유효. CDN 캐시 환경에서는 만료돼 403.
    """
    m = re.search(r'(https://job-hub-files[^\s"\'<>]+\.html[^\s"\'<>]*)', payload)
    return m.group(1) if m else None


def _extract_with_playwright(url: str, timeout_seconds: int = 32) -> str:
    """Node.js Playwright로 URL을 렌더링해 본문 텍스트 반환.

    JS 렌더링 후 DOM(iframe 포함)에서 텍스트를 추출하므로 동적 콘텐츠도 포함.
    Chromium이 없거나 timeout 초과 시 빈 문자열 반환 (caller가 fallback 처리).
    """
    script_path = Path(__file__).parent.parent.parent / "tools" / "playwright_extract.cjs"
    if not script_path.exists():
        return ""

    try:
        result = subprocess.run(
            ["node", str(script_path), url, str(timeout_seconds * 1000 - 3000)],
            capture_output=True,
            timeout=timeout_seconds,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0 and result.stdout.strip():
            return clean_text(result.stdout)
        return ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def extract_url(url: str, *, timeout_seconds: int = 10, max_bytes: int = 2_000_000) -> TextExtractionResult:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise TextExtractionError("URL은 http 또는 https로 시작해야 합니다.")

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; JD-Fit-Roadmap/0.1; +local-project)",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(max_bytes + 1)
            content_type = response.headers.get("Content-Type", "")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TextExtractionError("URL 본문을 가져오지 못했습니다. 채용공고 본문을 직접 붙여넣어 주세요.") from exc

    warnings: list[str] = []
    if len(raw) > max_bytes:
        raw = raw[:max_bytes]
        warnings.append("URL 응답이 커서 앞부분만 추출했습니다.")

    html = _decode_html(raw, content_type)

    # ── 잡코리아 RSC 분기 ─────────────────────────────────────────────
    host = parsed.hostname or ""
    if host.endswith("jobkorea.co.kr"):
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        job_title = _extract_jobkorea_workfield(payload)
        visible = extract_visible_text_from_html(html)
        if skills:
            # visible에 JD 본문 마커가 없으면 iframe에만 본문이 있는 것 → Playwright 보완
            # 숫자 threshold 대신 의미 기반 체크: 마커 없으면 메타데이터뿐
            _JD_MARKERS = (
                "담당업무", "자격요건", "우대사항", "주요업무", "필수조건",
                "이런 업무", "이런 분들", "이런 기술",
                "[담당", "[자격", "하는 일", "업무내용",
            )
            has_jd_body = any(m in visible for m in _JD_MARKERS)
            body = visible if has_jd_body else _extract_with_playwright(url)
            return TextExtractionResult(
                text=body or visible or f"[잡코리아 공고] {job_title or ''}",
                source_type="url",
                extractor="jobkorea_rsc",
                warnings=warnings,
                structured_skills=skills,
                job_title=job_title,
            )
        else:
            # skills=[] → S3 description URL 시도 (pre-signed, 페이지가 fresh하면 접근 가능)
            jd_body = ""
            desc_url = _extract_jobkorea_description_url(payload)
            if desc_url:
                try:
                    desc_req = Request(
                        desc_url,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; JD-Fit-Roadmap/0.1)"},
                    )
                    with urlopen(desc_req, timeout=8) as desc_resp:
                        desc_html = desc_resp.read(500_000).decode("utf-8", errors="replace")
                    jd_body = extract_visible_text_from_html(desc_html)
                except Exception:
                    pass  # 403 (만료) 또는 네트워크 오류 → fallback

            if jd_body:
                return TextExtractionResult(
                    text=(visible + " " + jd_body).strip(),
                    source_type="url",
                    extractor="jobkorea_description",
                    warnings=warnings,
                    structured_skills=[],
                    job_title=job_title,
                )
            # Playwright fallback: S3 URL 만료 또는 부재 시 브라우저 렌더링 시도
            pw_text = _extract_with_playwright(url)
            if len(pw_text) >= 200:
                return TextExtractionResult(
                    text=pw_text,
                    source_type="url",
                    extractor="jobkorea_playwright",
                    warnings=warnings,
                    structured_skills=[],
                    job_title=job_title,
                )
            return TextExtractionResult(
                text=visible,
                source_type="url",
                extractor="jobkorea_meta_only",
                warnings=warnings + [
                    "이 공고에서 구조화된 기술 정보를 찾지 못했습니다. "
                    "본문을 직접 붙여넣어 주세요."
                ],
                structured_skills=[],
                job_title=job_title,
            )

    text = extract_visible_text_from_html(html)
    if len(text) < 200:
        # 정적 HTML이 너무 짧음 → JS 렌더링 시도 (SPA/CSR 사이트 대응)
        pw_text = _extract_with_playwright(url)
        if len(pw_text) >= 200:
            return TextExtractionResult(
                text=pw_text,
                source_type="url",
                extractor="playwright",
                warnings=warnings,
            )
        if len(text) < 20:
            raise TextExtractionError(
                "URL에서 충분한 본문을 추출하지 못했습니다. 채용공고 본문을 직접 붙여넣어 주세요."
            )
    return TextExtractionResult(
        text=text,
        source_type="url",
        extractor="html_parser",
        warnings=warnings,
    )


def extract_visible_text_from_html(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    parser.close()
    return clean_text(" ".join(parser.parts))


def _decode_html(raw: bytes, content_type: str) -> str:
    charset_match = re.search(r"charset=([\w.-]+)", content_type, flags=re.IGNORECASE)
    encodings = [charset_match.group(1)] if charset_match else []
    encodings.extend(["utf-8", "cp949"])
    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def _extract_pdf_with_ocr(content: bytes) -> tuple[str, list[str]]:
    """pdf2image + pytesseract OCR. 패키지 미설치 시 빈 문자열 반환 (graceful skip)."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError:
        return "", []

    try:
        images = convert_from_bytes(content, dpi=200)
        parts: list[str] = []
        for img in images:
            text = pytesseract.image_to_string(img, lang="kor+eng")
            if text.strip():
                parts.append(text.strip())
        result = clean_text("\n".join(parts))
        warnings = (
            [
                "스캔 PDF를 OCR로 처리했습니다. "
                "텍스트 인식 정확도가 낮을 수 있으니 미리보기에서 확인 후 수정하세요."
            ]
            if result
            else []
        )
        return result, warnings
    except Exception:
        return "", []


class _VisibleTextParser(HTMLParser):
    ignored_tags = {"script", "style", "noscript", "svg", "nav", "footer", "header"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignore_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.ignored_tags:
            self._ignore_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.ignored_tags and self._ignore_depth:
            self._ignore_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignore_depth:
            return
        text = data.strip()
        if text:
            self.parts.append(text)
