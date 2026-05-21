from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import re

from app.schemas import EvidenceItem, MissingSkill, OwnedSkill, RequiredSkill


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TAXONOMY_PATH = DATA_DIR / "skill_taxonomy.json"
RULES_PATH = DATA_DIR / "analyzer_rules.json"


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class JobGroupDefinition:
    name: str
    classifier_keywords: tuple[str, ...]
    skills: tuple[SkillDefinition, ...]


@dataclass(frozen=True)
class AnalyzerConfig:
    job_groups: tuple[JobGroupDefinition, ...]
    required_keywords: tuple[str, ...]
    preferred_keywords: tuple[str, ...]
    negation_patterns: tuple[str, ...]
    required_missing_score: float
    preferred_missing_score: float
    explicit_negation_bonus: float
    max_gap_score: float
    gap_levels: tuple[tuple[float, str], ...]
    importance_weights: dict[str, float]


@dataclass
class SkillAnalysis:
    predicted_job: str
    fit_score: float
    required_skills: list[RequiredSkill]
    owned_skills: list[OwnedSkill]
    missing_skills: list[MissingSkill]


@lru_cache(maxsize=1)
def load_analyzer_config() -> AnalyzerConfig:
    with TAXONOMY_PATH.open("r", encoding="utf-8") as file:
        taxonomy = json.load(file)
    with RULES_PATH.open("r", encoding="utf-8") as file:
        rules = json.load(file)

    job_groups = []
    for group in taxonomy["job_groups"]:
        skills = tuple(
            SkillDefinition(name=item["name"], aliases=tuple(item["aliases"]))
            for item in group["skills"]
        )
        job_groups.append(
            JobGroupDefinition(
                name=group["name"],
                classifier_keywords=tuple(group["classifier_keywords"]),
                skills=skills,
            )
        )

    gap_scores = rules["gap_scores"]
    return AnalyzerConfig(
        job_groups=tuple(job_groups),
        required_keywords=tuple(rules["required_keywords"]),
        preferred_keywords=tuple(rules["preferred_keywords"]),
        negation_patterns=tuple(rules["negation_patterns"]),
        required_missing_score=float(gap_scores["required_missing"]),
        preferred_missing_score=float(gap_scores["preferred_missing"]),
        explicit_negation_bonus=float(gap_scores["explicit_negation_bonus"]),
        max_gap_score=float(gap_scores["max"]),
        gap_levels=tuple(
            (float(item["min"]), item["label"])
            for item in sorted(rules["gap_levels"], key=lambda row: row["min"], reverse=True)
        ),
        importance_weights={
            key: float(value) for key, value in rules["importance_weights"].items()
        },
    )


def _split_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?。])\s+|\n+", text)
        if sentence.strip()
    ]


def _contains(text: str, value: str) -> bool:
    return re.search(re.escape(value), text, flags=re.IGNORECASE) is not None


def _contains_any(text: str, values: tuple[str, ...]) -> bool:
    return any(_contains(text, value) for value in values)


def _skill_mentioned(sentence: str, skill: SkillDefinition) -> bool:
    return _contains_any(sentence, skill.aliases)


def _all_skills(config: AnalyzerConfig) -> list[SkillDefinition]:
    by_name: dict[str, SkillDefinition] = {}
    for group in config.job_groups:
        for skill in group.skills:
            if skill.name not in by_name:
                by_name[skill.name] = skill
    return list(by_name.values())


def _is_negated(sentence: str, config: AnalyzerConfig) -> bool:
    normalized = re.sub(r"\s+", " ", sentence)
    return _contains_any(normalized, config.negation_patterns)


def _importance(sentence: str, config: AnalyzerConfig) -> str:
    if _contains_any(sentence, config.preferred_keywords) and not _contains_any(
        sentence, config.required_keywords
    ):
        return "우대"
    return "필수"


def _strongest_importance(importances: list[str]) -> str:
    return "필수" if "필수" in importances else "우대"


def _evidence_for_skill(
    text: str,
    skill: SkillDefinition,
    source: str,
    config: AnalyzerConfig,
    *,
    allow_negated: bool,
) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for sentence in _split_sentences(text):
        if not _skill_mentioned(sentence, skill):
            continue
        if not allow_negated and _is_negated(sentence, config):
            continue
        evidence.append(EvidenceItem(text=sentence, source=source))
    return evidence


def _predict_job(job_text: str, config: AnalyzerConfig) -> str:
    scores: dict[str, int] = {}
    for group in config.job_groups:
        score = sum(1 for keyword in group.classifier_keywords if _contains(job_text, keyword))
        scores[group.name] = score

    best_job, best_score = max(scores.items(), key=lambda item: item[1])
    return best_job if best_score > 0 else "분류 보류"


def _gap_score(importance: str, explicit_negation: bool, config: AnalyzerConfig) -> float:
    base_score = (
        config.required_missing_score
        if importance == "필수"
        else config.preferred_missing_score
    )
    if explicit_negation:
        base_score += config.explicit_negation_bonus
    return min(config.max_gap_score, base_score)


def _gap_level(score: float, config: AnalyzerConfig) -> str:
    for threshold, label in config.gap_levels:
        if score >= threshold:
            return label
    return config.gap_levels[-1][1]


def _required_skills(
    job_text: str,
    config: AnalyzerConfig,
) -> list[tuple[RequiredSkill, str]]:
    required: list[tuple[RequiredSkill, str]] = []
    for skill in _all_skills(config):
        evidence = _evidence_for_skill(
            job_text,
            skill,
            "job_posting",
            config,
            allow_negated=False,
        )
        if not evidence:
            continue
        importances = [_importance(item.text, config) for item in evidence]
        importance = _strongest_importance(importances)
        required.append(
            (
                RequiredSkill(
                    skill=skill.name,
                    importance=importance,
                    evidence=evidence,
                ),
                skill.name,
            )
        )
    return required


def _owned_skills(candidate_text: str, config: AnalyzerConfig) -> list[OwnedSkill]:
    owned: list[OwnedSkill] = []
    for skill in _all_skills(config):
        evidence = _evidence_for_skill(
            candidate_text,
            skill,
            "candidate",
            config,
            allow_negated=False,
        )
        if evidence:
            owned.append(OwnedSkill(skill=skill.name, evidence=evidence))
    return owned


def _has_negated_candidate_mention(
    candidate_text: str,
    skill_name: str,
    config: AnalyzerConfig,
) -> bool:
    skill = next((item for item in _all_skills(config) if item.name == skill_name), None)
    if skill is None:
        return False
    return any(
        _skill_mentioned(sentence, skill) and _is_negated(sentence, config)
        for sentence in _split_sentences(candidate_text)
    )


def _fit_score(
    required: list[RequiredSkill],
    missing: list[MissingSkill],
    config: AnalyzerConfig,
) -> float:
    if not required:
        return 100.0

    gap_by_skill = {item.skill: item.gap_score for item in missing}
    total_weight = 0.0
    weighted_gap = 0.0
    for item in required:
        weight = config.importance_weights.get(item.importance, 1.0)
        total_weight += weight
        weighted_gap += gap_by_skill.get(item.skill, 0.0) * weight

    if total_weight == 0:
        return 100.0
    return round(max(0.0, 100.0 - (weighted_gap / total_weight)), 1)


def analyze_skill_gap(job_text: str, candidate_text: str) -> SkillAnalysis:
    config = load_analyzer_config()
    required_pairs = _required_skills(job_text, config)
    required = [item for item, _ in required_pairs]
    owned = _owned_skills(candidate_text, config)
    owned_names = {item.skill for item in owned}

    missing: list[MissingSkill] = []
    for item in required:
        if item.skill in owned_names:
            continue
        explicit_negation = _has_negated_candidate_mention(candidate_text, item.skill, config)
        gap_score = _gap_score(item.importance, explicit_negation, config)
        missing.append(
            MissingSkill(
                skill=item.skill,
                gap_score=gap_score,
                gap_level=_gap_level(gap_score, config),
                importance=item.importance,
                evidence=f"채용공고에는 {item.skill} 역량이 {item.importance}로 나타나지만 지원자 자료에는 충분한 근거가 없음",
            )
        )

    return SkillAnalysis(
        predicted_job=_predict_job(job_text, config),
        fit_score=_fit_score(required, missing, config),
        required_skills=required,
        owned_skills=owned,
        missing_skills=missing,
    )
