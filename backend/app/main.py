from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    COutput,
    RecommendResponse,
    SkillGap,
    SkillRecommendation,
    WeeklyRoadmapItem,
)
from app.services.embedding_retriever import (
    CHUNKING_STRATEGY,
    RetrieverInfo,
    build_retriever,
)
from app.services.resource_loader import SAMPLE_PATH, load_resources
from app.services.retriever import TfidfRetriever
from app.services.roadmap_generator import distribute_weeks, generate_roadmap
from app.services.report_generator import generate_product_report, generate_report
from app.services.scorer import score_resource
from app.services.skill_analyzer import analyze_skill_gap
from app.services.text_extractor import extract_from_text_source

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


def _build_skill_recommendations(
    c_output: COutput,
    top_k: int,
    user_difficulty: str = "기초",
) -> tuple[list[SkillRecommendation], RetrieverInfo]:
    resources = load_resources()
    try:
        retriever, retriever_info = build_retriever(resources)
    except Exception:
        retriever = TfidfRetriever(resources)
        retriever_info = RetrieverInfo(
            retrieval_mode="tfidf_fallback",
            embedding_model="none",
            chunking_strategy=CHUNKING_STRATEGY,
        )

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
        try:
            candidates = retriever.search(query, limit=max(12, top_k * 4))
        except Exception:
            retriever = TfidfRetriever(resources)
            retriever_info = RetrieverInfo(
                retrieval_mode="tfidf_fallback",
                embedding_model="none",
                chunking_strategy=CHUNKING_STRATEGY,
            )
            candidates = retriever.search(query, limit=max(12, top_k * 4))
        scored = [
            score_resource(
                resource=resource,
                semantic_similarity=similarity,
                skill=gap.skill,
                predicted_job=c_output.predicted_job,
                user_difficulty=user_difficulty,
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

    return skill_recommendations, retriever_info


@app.post("/recommend", response_model=RecommendResponse)
def recommend(c_output: COutput, top_k: int = 3) -> RecommendResponse:
    if top_k < 1 or top_k > 10:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")

    skill_recommendations, retriever_info = _build_skill_recommendations(
        c_output=c_output,
        top_k=top_k,
        user_difficulty="기초",
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
            "100 * (0.55 * semantic_similarity + 0.20 * skill_match + "
            "0.10 * job_group_match + 0.10 * difficulty_match + 0.05 * (reliability / 5))"
        ),
        rag_scope_note=(
            "learning_resources.csv에 정리한 큐레이션 학습자료 DB에서 검색합니다. "
            "웹 전체 검색 결과가 아닙니다."
        ),
        retrieval_mode=retriever_info.retrieval_mode,
        embedding_model=retriever_info.embedding_model,
        chunking_strategy=retriever_info.chunking_strategy,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, top_k: int = 3) -> AnalyzeResponse:
    if top_k < 1 or top_k > 10:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")

    job_text = extract_from_text_source(request.job_posting.text or "")
    candidate_text = " ".join(
        extract_from_text_source(material.text)
        for material in request.candidate_materials
        if material.text
    )

    if len(job_text) < 20:
        raise HTTPException(status_code=400, detail="job_posting text is too short")
    if len(candidate_text) < 20:
        raise HTTPException(status_code=400, detail="candidate text is too short")

    analysis = analyze_skill_gap(job_text=job_text, candidate_text=candidate_text)
    c_output = COutput(
        predicted_job=analysis.predicted_job,
        fit_score=analysis.fit_score,
        matched_skills=[item.skill for item in analysis.owned_skills],
        skill_gaps=[
            SkillGap(
                skill=item.skill,
                gap_score=item.gap_score,
                gap_level=item.gap_level,
                importance=item.importance,
                evidence=item.evidence,
            )
            for item in analysis.missing_skills
        ],
    )
    skill_recommendations, retriever_info = _build_skill_recommendations(
        c_output=c_output,
        top_k=top_k,
        user_difficulty=request.roadmap_preferences.difficulty,
    )

    missing_skill_names = [item.skill for item in analysis.missing_skills]
    roadmap_rows = distribute_weeks(missing_skill_names, request.roadmap_preferences)
    titles_by_skill = {
        item.skill: [recommendation.resource.title for recommendation in item.recommendations[:2]]
        for item in skill_recommendations
    }
    weekly_roadmap = [
        WeeklyRoadmapItem(
            week=row["week"],
            goal=row["goal"],
            skills=row["skills"],
            recommended_titles=titles_by_skill.get(row["skills"][0], []) if row["skills"] else [],
            practice=row["practice"],
        )
        for row in roadmap_rows
    ]
    report = generate_product_report(
        predicted_job=analysis.predicted_job,
        fit_score=analysis.fit_score,
        missing_skills=analysis.missing_skills,
        weekly_roadmap=weekly_roadmap,
        preferences=request.roadmap_preferences,
    )

    return AnalyzeResponse(
        predicted_job=analysis.predicted_job,
        fit_score=analysis.fit_score,
        roadmap_preferences=request.roadmap_preferences,
        required_skills=analysis.required_skills,
        owned_skills=analysis.owned_skills,
        missing_skills=analysis.missing_skills,
        recommended_resources=skill_recommendations,
        weekly_roadmap=weekly_roadmap,
        report=report,
        scoring_formula=(
            "100 * (0.55 * semantic_similarity + 0.20 * skill_match + "
            "0.10 * job_group_match + 0.10 * difficulty_match + 0.05 * (reliability / 5))"
        ),
        rag_scope_note="learning_resources.csv에 정리한 큐레이션 학습자료 DB에서 검색합니다.",
        retrieval_mode=retriever_info.retrieval_mode,
        embedding_model=retriever_info.embedding_model,
        chunking_strategy=retriever_info.chunking_strategy,
    )
