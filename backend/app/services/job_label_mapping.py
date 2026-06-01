from __future__ import annotations


LABEL_ORDER = ["ai", "backend", "data_analyst", "frontend"]

INDEX_TO_LABEL = {
    0: "ai",
    1: "backend",
    2: "data_analyst",
    3: "frontend",
}

LABEL_TO_JOB = {
    "ai": "AI/ML 엔지니어",
    "backend": "백엔드 개발자",
    "data_analyst": "데이터 분석가",
    "frontend": "프론트엔드 개발자",
}


def to_job_name(label: str) -> str:
    try:
        return LABEL_TO_JOB[label]
    except KeyError as exc:
        raise ValueError(f"Unknown job label: {label}") from exc
