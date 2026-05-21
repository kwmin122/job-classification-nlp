from __future__ import annotations

from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    skill: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    evidence: str


class COutput(BaseModel):
    predicted_job: str
    fit_score: float = Field(ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[SkillGap]


class Resource(BaseModel):
    id: str
    job_group: str
    skill: str
    sub_skill: str
    title: str
    description: str
    url: str
    type: str
    level: str
    language: str
    free_or_paid: str
    estimated_time: str
    reliability: int = Field(ge=1, le=5)
    reason: str


class ResourceRecommendation(BaseModel):
    resource: Resource
    semantic_similarity: float
    skill_match: float
    job_group_match: float
    reliability_norm: float
    recommend_score: float


class SkillRecommendation(BaseModel):
    skill: str
    gap_score: float
    gap_level: str
    importance: str
    evidence: str
    query: str
    recommendations: list[ResourceRecommendation]


class RoadmapItem(BaseModel):
    priority: int
    skill: str
    gap_score: float
    gap_level: str
    focus: str
    steps: list[str]
    recommended_titles: list[str]
    practice_project: str


class RecommendResponse(BaseModel):
    predicted_job: str
    fit_score: float
    matched_skills: list[str]
    top_priority_skill: str | None
    skill_recommendations: list[SkillRecommendation]
    roadmap: list[RoadmapItem]
    report: str
    scoring_formula: str
    rag_scope_note: str
    retrieval_mode: str
    embedding_model: str
    chunking_strategy: str
