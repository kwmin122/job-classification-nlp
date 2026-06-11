"""
이미지 기반 채용공고(JD 포스터 이미지) OCR — 크로스플랫폼(easyocr, 순수 pip).

linkareer 등은 직무 내용을 텍스트가 아니라 큰 이미지(포스터)로 올린다.
텍스트 크롤만으로는 요구역량을 못 읽으므로, 그 이미지를 OCR해 JD 텍스트를 복원한다.

- 엔진: easyocr (torch 기반, Windows/macOS/Linux 동일 동작). 첫 호출 시 모델 자동 다운로드.
- 미설치/실패 시 빈 문자열 반환 (graceful — 호출부가 fallback).
"""
from __future__ import annotations
import io
import threading
from urllib.request import Request, urlopen

_reader = None
_lock = threading.Lock()


def _get_reader():
    global _reader
    if _reader is None:
        with _lock:
            if _reader is None:
                import easyocr  # 지연 import (미설치 시 ImportError → 호출부 graceful)
                _reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
    return _reader


def ocr_image_bytes(data: bytes) -> str:
    """이미지 바이트 → 인식 텍스트(공백 결합). 실패 시 ''."""
    try:
        import numpy as np
        from PIL import Image
        img = Image.open(io.BytesIO(data)).convert("RGB")
        lines = _get_reader().readtext(np.array(img), detail=0, paragraph=True)
        return " ".join(lines)
    except Exception:
        return ""


def ocr_image_url(url: str, *, timeout: int = 20, max_bytes: int = 12_000_000) -> str:
    """이미지 URL 다운로드 후 OCR. 실패 시 ''."""
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; JD-Fit-Roadmap/0.1)"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read(max_bytes)
        return ocr_image_bytes(data)
    except Exception:
        return ""


def ocr_image_urls(urls: list[str], *, limit: int = 4) -> str:
    """여러 이미지 URL을 순서대로 OCR해 결합 (최대 limit개)."""
    out = []
    for u in urls[:limit]:
        t = ocr_image_url(u)
        if t:
            out.append(t)
    return " ".join(out)
