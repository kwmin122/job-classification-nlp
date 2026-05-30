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


def difficulty_match(user_difficulty: str, resource: Resource) -> float:
    matrix = {
        "입문": {"beginner": 1.0, "intermediate": 0.5, "advanced": 0.0},
        "기초": {"beginner": 0.8, "intermediate": 1.0, "advanced": 0.3},
        "실무": {"beginner": 0.3, "intermediate": 1.0, "advanced": 0.7},
        "심화": {"beginner": 0.0, "intermediate": 0.6, "advanced": 1.0},
    }
    return matrix.get(user_difficulty, {}).get(resource.level, 0.5)


def score_resource(
    resource: Resource,
    semantic_similarity: float,
    skill: str,
    predicted_job: str,
    user_difficulty: str = "기초",
) -> ResourceRecommendation:
    semantic = normalize_similarity(semantic_similarity)
    skill_score = skill_match(skill, resource)
    job_score = job_group_match(predicted_job, resource)
    difficulty_score = difficulty_match(user_difficulty, resource)
    reliability_norm = resource.reliability / 5

    recommend_score = 100 * (
        0.50 * semantic
        + 0.20 * skill_score
        + 0.05 * job_score
        + 0.20 * difficulty_score
        + 0.05 * reliability_norm
    )

    return ResourceRecommendation(
        resource=resource,
        semantic_similarity=round(semantic, 4),
        skill_match=skill_score,
        job_group_match=job_score,
        difficulty_match=difficulty_score,
        reliability_norm=round(reliability_norm, 2),
        recommend_score=round(recommend_score, 1),
    )
