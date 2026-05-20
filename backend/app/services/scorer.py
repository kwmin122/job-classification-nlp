from __future__ import annotations

from app.schemas import Resource, ResourceRecommendation


def normalize_similarity(value: float) -> float:
    return max(0.0, min(1.0, value))


def skill_match(skill: str, resource: Resource) -> float:
    target = skill.casefold()
    haystack = " ".join(
        [
            resource.skill,
            resource.sub_skill,
            resource.title,
            resource.description,
            resource.reason,
        ]
    ).casefold()
    return 1.0 if target in haystack else 0.0


def job_group_match(predicted_job: str, resource: Resource) -> float:
    return 1.0 if predicted_job == resource.job_group else 0.0


def score_resource(
    resource: Resource,
    semantic_similarity: float,
    skill: str,
    predicted_job: str,
) -> ResourceRecommendation:
    semantic = normalize_similarity(semantic_similarity)
    skill_score = skill_match(skill, resource)
    job_score = job_group_match(predicted_job, resource)
    reliability_norm = resource.reliability / 5

    recommend_score = 100 * (
        0.6 * semantic
        + 0.2 * skill_score
        + 0.1 * job_score
        + 0.1 * reliability_norm
    )

    return ResourceRecommendation(
        resource=resource,
        semantic_similarity=round(semantic, 4),
        skill_match=skill_score,
        job_group_match=job_score,
        reliability_norm=round(reliability_norm, 2),
        recommend_score=round(recommend_score, 1),
    )

