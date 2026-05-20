from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import COutput, RecommendResponse, SkillRecommendation
from app.services.resource_loader import SAMPLE_PATH, load_resources
from app.services.retriever import TfidfRetriever
from app.services.roadmap_generator import generate_roadmap
from app.services.report_generator import generate_report
from app.services.scorer import score_resource

app = FastAPI(title="JD Skill Gap RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "resource_count": len(load_resources())}


@app.get("/sample")
def sample() -> dict:
    with SAMPLE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/resources")
def resources() -> dict:
    return {"resources": [resource.model_dump() for resource in load_resources()]}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(c_output: COutput, top_k: int = 3) -> RecommendResponse:
    if top_k < 1 or top_k > 10:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")

    resources = load_resources()
    retriever = TfidfRetriever(resources)
    skill_recommendations: list[SkillRecommendation] = []

    sorted_gaps = sorted(c_output.skill_gaps, key=lambda gap: gap.gap_score, reverse=True)
    for gap in sorted_gaps:
        query = " ".join(
            [
                c_output.predicted_job,
                gap.skill,
                gap.gap_level,
                gap.importance,
                gap.evidence,
            ]
        )
        candidates = retriever.search(query, limit=max(12, top_k * 4))
        scored = [
            score_resource(
                resource=resource,
                semantic_similarity=similarity,
                skill=gap.skill,
                predicted_job=c_output.predicted_job,
            )
            for resource, similarity in candidates
        ]
        scored.sort(key=lambda item: item.recommend_score, reverse=True)
        skill_matched = [item for item in scored if item.skill_match > 0]
        selected = skill_matched[:top_k]
        if len(selected) < top_k:
            selected_resource_ids = {item.resource.id for item in selected}
            selected.extend(
                item for item in scored if item.resource.id not in selected_resource_ids
            )
        skill_recommendations.append(
            SkillRecommendation(
                skill=gap.skill,
                gap_score=gap.gap_score,
                gap_level=gap.gap_level,
                importance=gap.importance,
                evidence=gap.evidence,
                query=query,
                recommendations=selected[:top_k],
            )
        )

    roadmap = generate_roadmap(skill_recommendations)
    report = generate_report(c_output, skill_recommendations, roadmap)
    top_priority_skill = skill_recommendations[0].skill if skill_recommendations else None

    return RecommendResponse(
        predicted_job=c_output.predicted_job,
        fit_score=c_output.fit_score,
        matched_skills=c_output.matched_skills,
        top_priority_skill=top_priority_skill,
        skill_recommendations=skill_recommendations,
        roadmap=roadmap,
        report=report,
        scoring_formula=(
            "100 * (0.6 * semantic_similarity + 0.2 * skill_match + "
            "0.1 * job_group_match + 0.1 * (reliability / 5))"
        ),
        rag_scope_note=(
            "This is curated learning-resource DB retrieval over learning_resources.csv, "
            "not open-web search."
        ),
    )
