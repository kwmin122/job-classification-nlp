from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    skill: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    evidence: str


class JobPostingInput(BaseModel):
    source_type: Literal["url", "text", "file"]
    url: str | None = None
    text: str = ""


class CandidateMaterialInput(BaseModel):
    source_type: Literal["text", "file"]
    label: str
    text: str = ""


class RoadmapPreferences(BaseModel):
    duration_weeks: Literal[2, 4, 8, 12]
    difficulty: Literal["입문", "기초", "실무", "심화"]
    intensity: Literal["가볍게", "보통", "집중"]


class EvidenceItem(BaseModel):
    text: str
    source: str


class RequiredSkill(BaseModel):
    skill: str
    importance: str
    evidence: list[EvidenceItem] = Field(default_factory=list)


class OwnedSkill(BaseModel):
    skill: str
    evidence: list[EvidenceItem] = Field(default_factory=list)


class MissingSkill(BaseModel):
    skill: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    evidence: str


class AnalyzeRequest(BaseModel):
    job_posting: JobPostingInput
    candidate_materials: list[CandidateMaterialInput]
    roadmap_preferences: RoadmapPreferences


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


class WeeklyRoadmapItem(BaseModel):
    week: int
    goal: str
    skills: list[str] = Field(default_factory=list)
    recommended_titles: list[str] = Field(default_factory=list)
    practice: str


class AnalyzeResponse(BaseModel):
    predicted_job: str
    fit_score: float = Field(ge=0, le=100)
    roadmap_preferences: RoadmapPreferences
    required_skills: list[RequiredSkill] = Field(default_factory=list)
    owned_skills: list[OwnedSkill] = Field(default_factory=list)
    missing_skills: list[MissingSkill] = Field(default_factory=list)
    recommended_resources: list[SkillRecommendation] = Field(default_factory=list)
    weekly_roadmap: list[WeeklyRoadmapItem] = Field(default_factory=list)
    report: str
    scoring_formula: str
    rag_scope_note: str
    retrieval_mode: str
    embedding_model: str
    chunking_strategy: str


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
