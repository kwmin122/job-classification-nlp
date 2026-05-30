from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    COutput,
    EvidenceItem,
    ExtractedText,
    MissingSkill,
    OwnedSkill,
    PartialSkill,
    RecommendResponse,
    RequiredSkill,
    SkillGap,
    SkillRecommendation,
    WeeklyRoadmapItem,
)
from app.services.c_part import run_c_part_analysis, normalize_skill_name, _filter_analyzable_skills
from app.services.embedding_retriever import (
    CHUNKING_STRATEGY,
    RetrieverInfo,
    build_retriever,
)
from app.services.job_classifier import classify_job
from app.services.resource_loader import load_resources
from app.services.roadmap_generator import distribute_weeks, generate_roadmap
from app.services.report_generator import generate_product_report, generate_report
from app.services.scorer import score_resource
from app.services.text_extractor import (
    TextExtractionError,
    extract_file_bytes,
    extract_from_text_source,
    extract_text_input,
    extract_url,
)

app = FastAPI(title="JD Skill Gap RAG API", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
local_cors_regex = (
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    if os.getenv("ALLOW_LOCALHOST_CORS", "1") == "1"
    else None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=local_cors_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "resource_count": len(load_resources())}


@app.get("/resources")
def resources() -> dict:
    return {"resources": [resource.model_dump() for resource in load_resources()]}


@app.post("/extract/job-posting", response_model=ExtractedText)
async def extract_job_posting(request: Request) -> ExtractedText:
    return await _extract_source(kind="job_posting", request=request)


@app.post("/extract/candidate-material", response_model=ExtractedText)
async def extract_candidate_material(request: Request) -> ExtractedText:
    return await _extract_source(kind="candidate_material", request=request)


async def _extract_source(kind: str, request: Request) -> ExtractedText:
    try:
        source_type, text, url, file_payload, label, source_name = await _read_source_payload(request)
        if kind == "candidate_material" and source_type == "url":
            raise TextExtractionError("지원자 자료는 URL 추출을 지원하지 않습니다. 텍스트 또는 PDF/TXT 파일을 사용해 주세요.")

        if source_type == "text":
            result = extract_text_input(text or "")
        elif source_type == "url":
            result = extract_url(url or "")
        elif source_type == "file":
            if file_payload is None:
                raise TextExtractionError("업로드된 파일이 없습니다.")
            content, filename, content_type = file_payload
            source_name = filename
            result = extract_file_bytes(content, filename=filename, content_type=content_type)
        else:
            raise TextExtractionError("지원하지 않는 입력 방식입니다.")
    except TextExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ExtractedText(
        kind=kind,  # type: ignore[arg-type]
        source_type=result.source_type,  # type: ignore[arg-type]
        label=label,
        source_name=source_name,
        text=result.text,
        char_count=len(result.text),
        warnings=result.warnings,
        extractor=result.extractor,
    )


async def _read_source_payload(
    request: Request,
) -> tuple[str, str | None, str | None, tuple[bytes, str | None, str | None] | None, str | None, str | None]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        source_type = str(form.get("source_type") or "file")
        text = str(form.get("text") or "") or None
        url = str(form.get("url") or "") or None
        label = str(form.get("label") or "") or None
        form_file = form.get("file")
        if form_file is None or not hasattr(form_file, "read"):
            file_payload = None
            source_name = None
        else:
            content = await form_file.read()
            filename = getattr(form_file, "filename", None)
            uploaded_content_type = getattr(form_file, "content_type", None)
            await form_file.close()
            file_payload = (content, filename, uploaded_content_type)
            source_name = filename
        return source_type, text, url, file_payload, label, source_name

    try:
        payload = await request.json()
    except Exception as exc:
        raise TextExtractionError("JSON 또는 multipart/form-data 요청이 필요합니다.") from exc
    source_type = str(payload.get("source_type") or "text")
    return (
        source_type,
        payload.get("text"),
        payload.get("url"),
        None,
        payload.get("label"),
        payload.get("url"),
    )


def _build_skill_recommendations(
    c_output: COutput,
    top_k: int,
    user_difficulty: str = "기초",
    openai_api_key: str | None = None,
) -> tuple[list[SkillRecommendation], RetrieverInfo]:
    targets = _recommendation_targets(c_output)
    if not targets:
        return [], RetrieverInfo(
            retrieval_mode="not_required",
            embedding_model="none",
            chunking_strategy=CHUNKING_STRATEGY,
        )

    resources = load_resources()
    api_key = _normalize_optional_secret(openai_api_key)
    try:
        retriever, retriever_info = build_retriever(resources, api_key=api_key)
    except Exception:
        retriever, retriever_info = build_retriever(resources, api_key="")

    skill_recommendations: list[SkillRecommendation] = []
    for target_type, gap in targets:
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
            from app.services.retriever import TfidfRetriever

            retriever = TfidfRetriever(resources)
            retriever_info = RetrieverInfo(
                retrieval_mode="tfidf_last_resort",
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
        job_matched = [item for item in skill_matched if item.job_group_match > 0]
        selected = job_matched[:top_k]
        if len(selected) < top_k:
            selected_resource_ids = {item.resource.id for item in selected}
            selected.extend(
                item for item in skill_matched if item.resource.id not in selected_resource_ids
            )
        if len(selected) < top_k:
            selected_resource_ids = {item.resource.id for item in selected}
            selected.extend(
                item for item in scored if item.resource.id not in selected_resource_ids
            )
        skill_recommendations.append(
            SkillRecommendation(
                target_type=target_type,
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


def _normalize_optional_secret(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _recommendation_targets(c_output: COutput) -> list[tuple[str, SkillGap | PartialSkill]]:
    gap_targets = sorted(c_output.skill_gaps, key=lambda gap: gap.gap_score, reverse=True)
    partial_targets = sorted(c_output.partial_skills, key=lambda gap: gap.gap_score, reverse=True)
    return [("gap", item) for item in gap_targets] + [
        ("partial", item) for item in partial_targets
    ]


def _evidence_from_text(text: str, source: str) -> list[EvidenceItem]:
    if not text:
        return []
    return [EvidenceItem(text=text, source=source)]


def _required_skills_from_c(result: dict) -> list[RequiredSkill]:
    return [
        RequiredSkill(
            skill=item["skill"],
            importance=item.get("importance", "필수"),
            evidence=_evidence_from_text(item.get("source_sentence", ""), "job_description"),
        )
        for item in result.get("required_skills", [])
    ]


def _owned_skills_from_c(result: dict) -> list[OwnedSkill]:
    owned_skills: list[OwnedSkill] = []
    for item in result.get("owned_skills", []):
        skill_name = item["skill"] if isinstance(item, dict) else str(item)
        evidence_text = item.get("evidence", "") if isinstance(item, dict) else ""
        owned_skills.append(
            OwnedSkill(
                skill=skill_name,
                evidence=_evidence_from_text(evidence_text, "candidate_text"),
            )
        )
    return owned_skills


def _missing_skills_from_c_output(c_output: COutput) -> list[MissingSkill]:
    return [
        MissingSkill(
            skill=item.skill,
            gap_score=item.gap_score,
            gap_level=item.gap_level,
            importance=item.importance,
            evidence=item.evidence,
        )
        for item in c_output.skill_gaps
    ]


def _determine_jd_quality(
    structured_skills: list[str],
    required_count: int,
) -> str:
    """공고 품질 판정: structured_skills 없고 required_skills < 3 → weak."""
    if not structured_skills and required_count < 3:
        return "weak"
    return "ok"


def _c_output_from_result(result: dict) -> COutput:
    if result.get("status") != "success":
        raise HTTPException(status_code=422, detail=result.get("message", "C analysis failed"))
    return COutput.model_validate(result)


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
            "100 * (0.50 * semantic_similarity + 0.20 * skill_match + "
            "0.05 * job_group_match + 0.20 * difficulty_match + 0.05 * (reliability / 5))"
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

    # ── Job posting 추출 (URL 또는 텍스트) ────────────────────────────
    job_structured_skills: list[str] = []
    job_title: str | None = None

    if request.job_posting.source_type == "url" and request.job_posting.url:
        job_extraction = extract_url(request.job_posting.url)
        job_text = job_extraction.text
        job_structured_skills = job_extraction.structured_skills
        job_title = job_extraction.job_title
    else:
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

    # ── explicit_required_skills 결정 ────────────────────────────────
    explicit_required_skills: list[str] | None = None
    classify_input = job_text  # 기본값

    if job_structured_skills:
        norm_skills = [normalize_skill_name(s) for s in job_structured_skills]
        analyzable = _filter_analyzable_skills(norm_skills)
        explicit_required_skills = analyzable if analyzable else None
        # BLOCK 1: classify_job 입력 보강
        signal = " ".join(filter(None, [job_title, *norm_skills]))
        classify_input = signal + "\n" + job_text

    classification = classify_job(classify_input)
    c_result = run_c_part_analysis(
        b_predicted_job=classification.job_label,
        jd_input=classify_input,
        candidate_input=candidate_text,
        explicit_required_skills=explicit_required_skills,
    )
    c_output = _c_output_from_result(c_result)
    predicted_job = c_output.predicted_job
    required_skills = _required_skills_from_c(c_result)
    jd_quality = _determine_jd_quality(
        structured_skills=job_structured_skills,
        required_count=len(c_result.get("required_skills", [])),
    )
    owned_skills = _owned_skills_from_c(c_result)
    missing_skills = _missing_skills_from_c_output(c_output)

    skill_recommendations, retriever_info = _build_skill_recommendations(
        c_output=c_output,
        top_k=top_k,
        user_difficulty=request.roadmap_preferences.difficulty,
        openai_api_key=request.openai_api_key,
    )

    roadmap_skill_names = [item.skill for item in skill_recommendations]
    roadmap_rows = distribute_weeks(roadmap_skill_names, request.roadmap_preferences)
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
        predicted_job=predicted_job,
        fit_score=c_output.fit_score,
        missing_skills=missing_skills,
        partial_skills=c_output.partial_skills,
        weekly_roadmap=weekly_roadmap,
        preferences=request.roadmap_preferences,
        owned_skills_count=len(owned_skills),
        jd_quality=jd_quality,
    )

    return AnalyzeResponse(
        predicted_job=predicted_job,
        job_label=classification.job_label,
        job_probabilities=classification.job_probabilities,
        classifier_source=classification.classifier_source,
        fit_score=c_output.fit_score,
        roadmap_preferences=request.roadmap_preferences,
        required_skills=required_skills,
        owned_skills=owned_skills,
        partial_skills=c_output.partial_skills,
        missing_skills=missing_skills,
        recommended_resources=skill_recommendations,
        weekly_roadmap=weekly_roadmap,
        report=report,
        scoring_formula=(
            "100 * (0.50 * semantic_similarity + 0.20 * skill_match + "
            "0.05 * job_group_match + 0.20 * difficulty_match + 0.05 * (reliability / 5))"
        ),
        rag_scope_note="learning_resources.csv에 정리한 큐레이션 학습자료 DB에서 검색합니다.",
        retrieval_mode=retriever_info.retrieval_mode,
        embedding_model=retriever_info.embedding_model,
        chunking_strategy=retriever_info.chunking_strategy,
        structured_skills=job_structured_skills,
        jd_quality=jd_quality,
    )
