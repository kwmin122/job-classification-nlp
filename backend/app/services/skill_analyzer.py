from __future__ import annotations

from dataclasses import dataclass

from app.schemas import EvidenceItem, MissingSkill, OwnedSkill, RequiredSkill


SKILL_KEYWORDS = [
    "Python",
    "SQL",
    "Docker",
    "AWS",
    "CI/CD",
    "Spring Boot",
    "React",
    "TypeScript",
    "PyTorch",
]


@dataclass
class SkillAnalysis:
    predicted_job: str
    fit_score: float
    required_skills: list[RequiredSkill]
    owned_skills: list[OwnedSkill]
    missing_skills: list[MissingSkill]


def _contains(text: str, skill: str) -> bool:
    return skill.casefold() in text.casefold()


def _predict_job(job_text: str) -> str:
    if "프론트엔드" in job_text or "React" in job_text:
        return "프론트엔드 개발자"
    if "AI" in job_text or "머신러닝" in job_text or "PyTorch" in job_text:
        return "AI/ML 엔지니어"
    if "데이터 분석" in job_text or "SQL" in job_text:
        return "데이터 분석가"
    return "백엔드 개발자"


def analyze_skill_gap(job_text: str, candidate_text: str) -> SkillAnalysis:
    required = [
        RequiredSkill(
            skill=skill,
            importance="필수",
            evidence=[EvidenceItem(text=skill, source="job_posting")],
        )
        for skill in SKILL_KEYWORDS
        if _contains(job_text, skill)
    ]
    owned = [
        OwnedSkill(
            skill=skill,
            evidence=[EvidenceItem(text=skill, source="candidate")],
        )
        for skill in SKILL_KEYWORDS
        if _contains(candidate_text, skill)
    ]
    owned_names = {item.skill for item in owned}
    missing = [
        MissingSkill(
            skill=item.skill,
            gap_score=80,
            gap_level="높음",
            importance=item.importance,
            evidence=f"채용공고에는 {item.skill} 역량이 요구되지만 지원자 자료에는 명확히 나타나지 않음",
        )
        for item in required
        if item.skill not in owned_names
    ]
    fit_score = 100.0
    if required:
        fit_score = round(100 * (len(required) - len(missing)) / len(required), 1)
    return SkillAnalysis(
        predicted_job=_predict_job(job_text),
        fit_score=fit_score,
        required_skills=required,
        owned_skills=owned,
        missing_skills=missing,
    )
