from __future__ import annotations

import re


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_from_text_source(value: str) -> str:
    return clean_text(value)
