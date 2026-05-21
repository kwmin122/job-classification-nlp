# User Roadmap Product Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the final user-facing flow where a job seeker submits a job posting and candidate materials, selects roadmap duration/difficulty/intensity, and receives skill-gap analysis, recommended learning resources, a weekly roadmap, and a report.

**Architecture:** The product uses a FastAPI backend for extraction, analysis, recommendation, roadmap generation, and report generation. The frontend is a Next.js local dashboard with user-facing input panels and evidence-based result panels. Recommendation uses `learning_resources.csv`, OpenAI `text-embedding-3-small` when available, and TF-IDF fallback for local reliability.

**Tech Stack:** FastAPI, Pydantic, Python unittest, CSV, NumPy cosine similarity, OpenAI embeddings, Next.js, TypeScript.

---

## Files

- Modify: `backend/app/schemas.py`
  - Add product request/response schemas: job posting input, candidate material input, roadmap preferences, missing skills, weekly roadmap.
- Create: `backend/app/services/text_extractor.py`
  - Extract text from pasted text, URLs, TXT files, and PDF files.
- Create: `backend/app/services/skill_analyzer.py`
  - Produce required skills, owned skills, missing skills, gap scores, and evidence.
- Modify: `backend/app/services/scorer.py`
  - Add difficulty preference scoring.
- Modify: `backend/app/services/roadmap_generator.py`
  - Generate weekly roadmap using duration, difficulty, and intensity.
- Modify: `backend/app/services/report_generator.py`
  - Include user preferences and weekly roadmap in the report.
- Modify: `backend/app/main.py`
  - Add `POST /analyze`.
- Create: `backend/tools/audit_learning_resources.py`
  - Validate resource DB quality.
- Create: `backend/tools/evaluate_recommendations.py`
  - Calculate Hit@K and Precision@K.
- Modify: `frontend/lib/types.ts`
  - Add product request/response types.
- Modify: `frontend/lib/api.ts`
  - Add `analyze()`.
- Create: `frontend/components/JobPostingInputPanel.tsx`
  - Job posting URL/text/file controls.
- Create: `frontend/components/CandidateInputPanel.tsx`
  - Candidate material text/file controls.
- Create: `frontend/components/RoadmapPreferencePanel.tsx`
  - Duration, difficulty, intensity controls.
- Modify: `frontend/app/page.tsx`
  - Replace static-result input flow with product input flow.
- Modify: `frontend/components/GapMatrix.tsx`
  - Show required/owned/missing evidence.
- Modify: `frontend/components/RoadmapPanel.tsx`
  - Show weekly roadmap.
- Modify: `frontend/components/ResourceRecommendations.tsx`
  - Show difficulty match and recommendation score.
- Create: `docs/evaluation-results.md`
  - Record actual evaluation command outputs.

---

## Task 1: Product Schemas

**Files:**
- Modify: `backend/app/schemas.py`
- Test: `backend/tests/test_product_schemas.py`

- [ ] **Step 1: Add schema tests**

```python
import unittest

from app.schemas import AnalyzeRequest, AnalyzeResponse, RoadmapPreferences


class ProductSchemaTest(unittest.TestCase):
    def test_analyze_request_accepts_user_inputs_and_preferences(self) -> None:
        request = AnalyzeRequest(
            job_posting={
                "source_type": "url",
                "url": "https://example.com/job",
                "text": "",
            },
            candidate_materials=[
                {
                    "source_type": "text",
                    "label": "자소서",
                    "text": "Spring Boot API 개발 경험이 있습니다.",
                }
            ],
            roadmap_preferences={
                "duration_weeks": 4,
                "difficulty": "입문",
                "intensity": "보통",
            },
        )
        self.assertEqual(request.roadmap_preferences.duration_weeks, 4)
        self.assertEqual(request.candidate_materials[0].label, "자소서")

    def test_roadmap_preferences_rejects_invalid_duration(self) -> None:
        with self.assertRaises(ValueError):
            RoadmapPreferences(duration_weeks=3, difficulty="입문", intensity="보통")

    def test_analyze_response_contains_product_outputs(self) -> None:
        response = AnalyzeResponse(
            predicted_job="백엔드 개발자",
            fit_score=75,
            roadmap_preferences={
                "duration_weeks": 4,
                "difficulty": "입문",
                "intensity": "보통",
            },
            required_skills=[],
            owned_skills=[],
            missing_skills=[],
            recommended_resources=[],
            weekly_roadmap=[],
            report="분석 리포트",
            scoring_formula="formula",
            rag_scope_note="curated db",
            retrieval_mode="tfidf_fallback",
            embedding_model="none",
            chunking_strategy="one resource row per chunk",
        )
        self.assertEqual(response.report, "분석 리포트")
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_product_schemas.py
```

Expected: fails because `AnalyzeRequest` does not exist.

- [ ] **Step 3: Implement schemas**

```python
from typing import Literal


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
```

- [ ] **Step 4: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_product_schemas.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas.py backend/tests/test_product_schemas.py
git commit -m "Add user product request schemas"
```

---

## Task 2: Text Extraction

**Files:**
- Create: `backend/app/services/text_extractor.py`
- Test: `backend/tests/test_text_extractor.py`

- [ ] **Step 1: Add tests**

```python
import unittest

from app.services.text_extractor import clean_text, extract_from_text_source


class TextExtractorTest(unittest.TestCase):
    def test_clean_text_removes_duplicate_spaces(self) -> None:
        self.assertEqual(clean_text("  Python   SQL\\n\\nDocker  "), "Python SQL Docker")

    def test_extract_from_text_source_returns_clean_text(self) -> None:
        result = extract_from_text_source("  Spring Boot   API 개발  ")
        self.assertEqual(result, "Spring Boot API 개발")
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_text_extractor.py
```

Expected: fails because module does not exist.

- [ ] **Step 3: Implement minimal extractor**

```python
from __future__ import annotations

import re


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_from_text_source(value: str) -> str:
    return clean_text(value)
```

- [ ] **Step 4: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_text_extractor.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/text_extractor.py backend/tests/test_text_extractor.py
git commit -m "Add text extraction service"
```

---

## Task 3: Skill Analysis Service

**Files:**
- Create: `backend/app/services/skill_analyzer.py`
- Test: `backend/tests/test_skill_analyzer.py`

- [ ] **Step 1: Add tests**

```python
import unittest

from app.services.skill_analyzer import analyze_skill_gap


class SkillAnalyzerTest(unittest.TestCase):
    def test_detects_missing_skill_from_job_posting(self) -> None:
        result = analyze_skill_gap(
            job_text="백엔드 개발자. Docker 기반 배포 경험과 AWS 운영 경험 필수.",
            candidate_text="Spring Boot와 MySQL 기반 API를 개발했습니다.",
        )
        missing_names = [item.skill for item in result.missing_skills]
        self.assertIn("Docker", missing_names)
        self.assertIn("AWS", missing_names)
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_skill_analyzer.py
```

Expected: fails because service does not exist.

- [ ] **Step 3: Implement deterministic first version**

Use the project skill basis as a deterministic dictionary. The first version should be transparent and testable before replacing internals with stronger NLP models.

```python
from __future__ import annotations

from dataclasses import dataclass

from app.schemas import EvidenceItem, MissingSkill, OwnedSkill, RequiredSkill


SKILL_KEYWORDS = ["Python", "SQL", "Docker", "AWS", "CI/CD", "Spring Boot", "React", "TypeScript", "PyTorch"]


@dataclass
class SkillAnalysis:
    predicted_job: str
    fit_score: float
    required_skills: list[RequiredSkill]
    owned_skills: list[OwnedSkill]
    missing_skills: list[MissingSkill]


def _contains(text: str, skill: str) -> bool:
    return skill.casefold() in text.casefold()


def analyze_skill_gap(job_text: str, candidate_text: str) -> SkillAnalysis:
    required = [
        RequiredSkill(skill=skill, importance="필수", evidence=[EvidenceItem(text=skill, source="job_posting")])
        for skill in SKILL_KEYWORDS
        if _contains(job_text, skill)
    ]
    owned = [
        OwnedSkill(skill=skill, evidence=[EvidenceItem(text=skill, source="candidate")])
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
    fit_score = 100 if not required else round(100 * (len(required) - len(missing)) / len(required), 1)
    return SkillAnalysis(
        predicted_job="백엔드 개발자",
        fit_score=fit_score,
        required_skills=required,
        owned_skills=owned,
        missing_skills=missing,
    )
```

- [ ] **Step 4: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_skill_analyzer.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/skill_analyzer.py backend/tests/test_skill_analyzer.py
git commit -m "Add deterministic skill gap analyzer"
```

---

## Task 4: Recommendation Scoring with Difficulty Preference

**Files:**
- Modify: `backend/app/services/scorer.py`
- Test: `backend/tests/test_scorer.py`

- [ ] **Step 1: Add tests**

```python
import unittest

from app.schemas import Resource
from app.services.scorer import difficulty_match, score_resource


def resource(level: str) -> Resource:
    return Resource(
        id="R1",
        job_group="백엔드 개발자",
        skill="Docker",
        sub_skill="컨테이너",
        title="Docker 입문",
        description="Docker 기본",
        url="https://example.com",
        type="공식문서",
        level=level,
        language="한국어",
        free_or_paid="무료",
        estimated_time="3시간",
        reliability=5,
        reason="Docker 보완",
    )


class ScorerTest(unittest.TestCase):
    def test_difficulty_match_prefers_beginner_for_intro_user(self) -> None:
        self.assertEqual(difficulty_match("입문", resource("beginner")), 1.0)
        self.assertEqual(difficulty_match("입문", resource("advanced")), 0.0)

    def test_score_resource_includes_difficulty(self) -> None:
        beginner = score_resource(resource("beginner"), 0.8, "Docker", "백엔드 개발자", "입문")
        advanced = score_resource(resource("advanced"), 0.8, "Docker", "백엔드 개발자", "입문")
        self.assertGreater(beginner.recommend_score, advanced.recommend_score)
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_scorer.py
```

Expected: fails because `difficulty_match` does not exist or signature mismatch.

- [ ] **Step 3: Implement difficulty scoring**

Update recommendation formula:

```python
def difficulty_match(user_difficulty: str, resource: Resource) -> float:
    matrix = {
        "입문": {"beginner": 1.0, "intermediate": 0.5, "advanced": 0.0},
        "기초": {"beginner": 0.8, "intermediate": 1.0, "advanced": 0.3},
        "실무": {"beginner": 0.3, "intermediate": 1.0, "advanced": 0.7},
        "심화": {"beginner": 0.0, "intermediate": 0.6, "advanced": 1.0},
    }
    return matrix[user_difficulty].get(resource.level, 0.5)
```

Use:

```python
recommend_score = 100 * (
    0.55 * semantic
    + 0.20 * skill_score
    + 0.10 * job_score
    + 0.10 * difficulty_score
    + 0.05 * reliability_norm
)
```

- [ ] **Step 4: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_scorer.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scorer.py backend/tests/test_scorer.py
git commit -m "Add difficulty-aware recommendation scoring"
```

---

## Task 5: Weekly Roadmap Generator

**Files:**
- Modify: `backend/app/services/roadmap_generator.py`
- Test: `backend/tests/test_roadmap_generator.py`

- [ ] **Step 1: Add tests**

```python
import unittest

from app.schemas import RoadmapPreferences
from app.services.roadmap_generator import distribute_weeks


class RoadmapGeneratorTest(unittest.TestCase):
    def test_distribute_weeks_uses_selected_duration(self) -> None:
        weeks = distribute_weeks(["Docker", "AWS"], RoadmapPreferences(duration_weeks=4, difficulty="입문", intensity="보통"))
        self.assertEqual(len(weeks), 4)
        self.assertEqual(weeks[0]["week"], 1)
        self.assertIn("Docker", weeks[0]["skills"])
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_roadmap_generator.py
```

Expected: fails because `distribute_weeks` does not exist.

- [ ] **Step 3: Implement weekly distribution**

```python
def distribute_weeks(skills: list[str], preferences: RoadmapPreferences) -> list[dict]:
    if not skills:
        return []
    weeks = []
    for week in range(1, preferences.duration_weeks + 1):
        skill = skills[min((week - 1) * len(skills) // preferences.duration_weeks, len(skills) - 1)]
        weeks.append(
            {
                "week": week,
                "goal": f"{skill} 학습 및 실습",
                "skills": [skill],
                "practice": f"{skill}을 적용한 작은 결과물을 만들고 정리하기",
            }
        )
    return weeks
```

- [ ] **Step 4: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_roadmap_generator.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/roadmap_generator.py backend/tests/test_roadmap_generator.py
git commit -m "Generate weekly roadmap from user preferences"
```

---

## Task 6: `/analyze` Integration API

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/report_generator.py`
- Test: `backend/tests/test_analyze_api.py`

- [ ] **Step 1: Add API test**

```python
import unittest

from fastapi.testclient import TestClient

from app.main import app


class AnalyzeApiTest(unittest.TestCase):
    def test_analyze_returns_user_centered_result(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/analyze",
            json={
                "job_posting": {
                    "source_type": "text",
                    "text": "백엔드 개발자. Docker 기반 배포 경험 필수.",
                },
                "candidate_materials": [
                    {
                        "source_type": "text",
                        "label": "자소서",
                        "text": "Spring Boot API를 개발했습니다.",
                    }
                ],
                "roadmap_preferences": {
                    "duration_weeks": 4,
                    "difficulty": "입문",
                    "intensity": "보통",
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["roadmap_preferences"]["duration_weeks"], 4)
        self.assertEqual(body["predicted_job"], "백엔드 개발자")
        self.assertTrue(any(item["skill"] == "Docker" for item in body["missing_skills"]))
        self.assertEqual(len(body["weekly_roadmap"]), 4)
        self.assertTrue(body["recommended_resources"])
        self.assertIn("Docker", body["report"])

    def test_analyze_rejects_short_candidate_text(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/analyze",
            json={
                "job_posting": {
                    "source_type": "text",
                    "text": "백엔드 개발자. Docker 기반 배포 경험 필수.",
                },
                "candidate_materials": [
                    {
                        "source_type": "text",
                        "label": "자소서",
                        "text": "짧음",
                    }
                ],
                "roadmap_preferences": {
                    "duration_weeks": 4,
                    "difficulty": "입문",
                    "intensity": "보통",
                },
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("candidate", response.json()["detail"])
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_analyze_api.py
```

Expected: fails because `/analyze` does not exist.

- [ ] **Step 3: Add product report function**

Append this function to `backend/app/services/report_generator.py`:

```python
from app.schemas import MissingSkill, RoadmapPreferences, WeeklyRoadmapItem


def generate_product_report(
    predicted_job: str,
    fit_score: float,
    missing_skills: list[MissingSkill],
    weekly_roadmap: list[WeeklyRoadmapItem],
    preferences: RoadmapPreferences,
) -> str:
    if not missing_skills:
        return (
            f"지원자는 {predicted_job} 직무 기준으로 {fit_score:.0f}점의 적합도를 보입니다. "
            "현재 입력에서는 뚜렷한 부족 역량이 확인되지 않았습니다. "
            "지원 자료에 프로젝트 성과와 사용 기술 근거를 더 구체적으로 작성하면 분석 신뢰도를 높일 수 있습니다."
        )

    top = sorted(missing_skills, key=lambda item: item.gap_score, reverse=True)[0]
    weeks = ", ".join(f"{item.week}주차 {item.goal}" for item in weekly_roadmap[:3])
    return (
        f"지원자는 {predicted_job} 직무 기준으로 {fit_score:.0f}점의 적합도를 보입니다. "
        f"가장 먼저 보완할 역량은 {top.skill}이며 gap score는 {top.gap_score:.0f}점입니다. "
        f"근거는 '{top.evidence}'입니다. "
        f"{preferences.duration_weeks}주 동안 현재 수준 {preferences.difficulty}, 학습 강도 {preferences.intensity} 기준으로 "
        f"{weeks} 순서로 학습하는 것을 추천합니다. "
        "이 리포트는 채용공고와 지원자 자료의 역량 격차, 그리고 큐레이션된 학습자료 DB 검색 결과를 바탕으로 생성되었습니다."
    )
```

- [ ] **Step 4: Implement shared recommendation helper and endpoint**

Modify `backend/app/main.py` imports:

```python
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    COutput,
    RecommendResponse,
    SkillGap,
    SkillRecommendation,
    WeeklyRoadmapItem,
)
from app.services.report_generator import generate_product_report, generate_report
from app.services.roadmap_generator import distribute_weeks, generate_roadmap
from app.services.skill_analyzer import analyze_skill_gap
from app.services.text_extractor import extract_from_text_source
```

Add this helper above `/recommend`:

```python
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
        selected = scored[:top_k]

        skill_recommendations.append(
            SkillRecommendation(
                skill=gap.skill,
                gap_score=gap.gap_score,
                gap_level=gap.gap_level,
                importance=gap.importance,
                evidence=gap.evidence,
                query=query,
                recommendations=selected,
            )
        )

    return skill_recommendations, retriever_info
```

Replace the repeated retrieval logic inside `/recommend` with:

```python
skill_recommendations, retriever_info = _build_skill_recommendations(
    c_output=c_output,
    top_k=top_k,
    user_difficulty="기초",
)
```

Then add `POST /analyze` below `/recommend`:

```python
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
```

- [ ] **Step 5: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_analyze_api.py
```

Expected: tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/main.py backend/app/services/report_generator.py backend/tests/test_analyze_api.py
git commit -m "Add user analyze endpoint"
```

---

## Task 7: Frontend Product Input Flow

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/lib/api.ts`
- Create: `frontend/components/JobPostingInputPanel.tsx`
- Create: `frontend/components/CandidateInputPanel.tsx`
- Create: `frontend/components/RoadmapPreferencePanel.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Add frontend types**

```ts
export type SourceType = "url" | "text" | "file";

export type RoadmapPreferences = {
  duration_weeks: 2 | 4 | 8 | 12;
  difficulty: "입문" | "기초" | "실무" | "심화";
  intensity: "가볍게" | "보통" | "집중";
};

export type AnalyzeRequest = {
  job_posting: {
    source_type: SourceType;
    url?: string;
    text: string;
  };
  candidate_materials: Array<{
    source_type: "text" | "file";
    label: string;
    text: string;
  }>;
  roadmap_preferences: RoadmapPreferences;
};

export type EvidenceItem = {
  text: string;
  source: string;
};

export type RequiredSkill = {
  skill: string;
  importance: string;
  evidence: EvidenceItem[];
};

export type OwnedSkill = {
  skill: string;
  evidence: EvidenceItem[];
};

export type WeeklyRoadmapItem = {
  week: number;
  goal: string;
  skills: string[];
  recommended_titles: string[];
  practice: string;
};

export type AnalyzeResponse = {
  predicted_job: string;
  fit_score: number;
  roadmap_preferences: RoadmapPreferences;
  required_skills: RequiredSkill[];
  owned_skills: OwnedSkill[];
  missing_skills: SkillGap[];
  recommended_resources: SkillRecommendation[];
  weekly_roadmap: WeeklyRoadmapItem[];
  report: string;
  scoring_formula: string;
  rag_scope_note: string;
  retrieval_mode: string;
  embedding_model: string;
  chunking_strategy: string;
};
```

- [ ] **Step 2: Add API client**

```ts
import type { AnalyzeRequest, AnalyzeResponse, COutput, RecommendResponse } from "./types";

export async function analyze(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseResponse<AnalyzeResponse>(response);
}
```

- [ ] **Step 3: Add job posting input panel**

Create `frontend/components/JobPostingInputPanel.tsx`:

```tsx
type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function JobPostingInputPanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="지원할 채용공고">
      <div className="section-heading">
        <p className="eyebrow">Target JD</p>
        <h2>지원할 채용공고</h2>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="채용공고 본문을 붙여넣으세요. 예: 주요업무, 자격요건, 우대사항"
        rows={10}
      />
    </section>
  );
}
```

- [ ] **Step 4: Add candidate input panel**

Create `frontend/components/CandidateInputPanel.tsx`:

```tsx
type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function CandidateInputPanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="내 지원 자료">
      <div className="section-heading">
        <p className="eyebrow">Candidate Evidence</p>
        <h2>내 지원 자료</h2>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="자소서, 이력서 요약, 포트폴리오 설명, GitHub README 내용을 붙여넣으세요."
        rows={10}
      />
    </section>
  );
}
```

- [ ] **Step 5: Add roadmap preference panel**

Create `frontend/components/RoadmapPreferencePanel.tsx`:

```tsx
import type { RoadmapPreferences } from "@/lib/types";

type Props = {
  value: RoadmapPreferences;
  onChange: (value: RoadmapPreferences) => void;
};

const durations = [2, 4, 8, 12] as const;
const difficulties = ["입문", "기초", "실무", "심화"] as const;
const intensities = ["가볍게", "보통", "집중"] as const;

export function RoadmapPreferencePanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="학습 목표">
      <div className="section-heading">
        <p className="eyebrow">Learning Goal</p>
        <h2>학습 목표</h2>
      </div>

      <div className="segmented-group">
        <span>기간</span>
        <div>
          {durations.map((duration) => (
            <button
              key={duration}
              type="button"
              className={value.duration_weeks === duration ? "selected" : ""}
              onClick={() => onChange({ ...value, duration_weeks: duration })}
            >
              {duration}주
            </button>
          ))}
        </div>
      </div>

      <div className="segmented-group">
        <span>현재 수준</span>
        <div>
          {difficulties.map((difficulty) => (
            <button
              key={difficulty}
              type="button"
              className={value.difficulty === difficulty ? "selected" : ""}
              onClick={() => onChange({ ...value, difficulty })}
            >
              {difficulty}
            </button>
          ))}
        </div>
      </div>

      <div className="segmented-group">
        <span>강도</span>
        <div>
          {intensities.map((intensity) => (
            <button
              key={intensity}
              type="button"
              className={value.intensity === intensity ? "selected" : ""}
              onClick={() => onChange({ ...value, intensity })}
            >
              {intensity}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 6: Replace primary page**

Replace `frontend/app/page.tsx` with:

```tsx
"use client";

import { useState } from "react";
import { CandidateInputPanel } from "@/components/CandidateInputPanel";
import { JobPostingInputPanel } from "@/components/JobPostingInputPanel";
import { RoadmapPreferencePanel } from "@/components/RoadmapPreferencePanel";
import { analyze } from "@/lib/api";
import type { AnalyzeResponse, RoadmapPreferences } from "@/lib/types";

export default function Home() {
  const [jobText, setJobText] = useState("");
  const [candidateText, setCandidateText] = useState("");
  const [preferences, setPreferences] = useState<RoadmapPreferences>({
    duration_weeks: 4,
    difficulty: "입문",
    intensity: "보통",
  });
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    setError(null);
    setIsLoading(true);
    try {
      const response = await analyze({
        job_posting: {
          source_type: "text",
          text: jobText,
        },
        candidate_materials: [
          {
            source_type: "text",
            label: "지원자 자료",
            text: candidateText,
          },
        ],
        roadmap_preferences: preferences,
      });
      setResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="product-topbar">
        <div>
          <p className="eyebrow">JD Fit Roadmap</p>
          <h1>지원 직무에 맞춘 학습 로드맵</h1>
          <p>채용공고와 내 지원 자료를 비교해 부족 역량과 학습 순서를 제안합니다.</p>
        </div>
      </header>

      <div className="dashboard-grid">
        <section className="input-stack" aria-label="분석 입력">
          <JobPostingInputPanel value={jobText} onChange={setJobText} />
          <CandidateInputPanel value={candidateText} onChange={setCandidateText} />
          <RoadmapPreferencePanel value={preferences} onChange={setPreferences} />
          <button className="primary-action" type="button" onClick={handleAnalyze} disabled={isLoading}>
            {isLoading ? "분석 중" : "분석 시작"}
          </button>
          {error ? <p className="error-message">{error}</p> : null}
        </section>

        <section className="workspace" aria-label="분석 결과">
          <header className="workspace-header">
            <div>
              <p className="eyebrow">Analysis Result</p>
              <h2>보완 필요 역량과 로드맵</h2>
            </div>
            <div className="status-chip">{result ? "분석 완료" : "입력 대기"}</div>
          </header>

          {result ? (
            <>
              <section className="summary-grid">
                <div><span>예측 직무</span><strong>{result.predicted_job}</strong></div>
                <div><span>적합도</span><strong>{result.fit_score.toFixed(0)}점</strong></div>
                <div><span>부족 역량</span><strong>{result.missing_skills.length}개</strong></div>
              </section>

              <section className="result-panel">
                <h3>부족 역량</h3>
                {result.missing_skills.map((skill) => (
                  <article key={skill.skill} className="skill-row">
                    <strong>{skill.skill}</strong>
                    <span>{skill.gap_level} / {skill.gap_score.toFixed(0)}점</span>
                    <p>{skill.evidence}</p>
                  </article>
                ))}
              </section>

              <section className="result-panel">
                <h3>추천 자료</h3>
                {result.recommended_resources.map((group) => (
                  <article key={group.skill} className="resource-group">
                    <h4>{group.skill}</h4>
                    {group.recommendations.map((item) => (
                      <a key={item.resource.id} href={item.resource.url} target="_blank" rel="noreferrer">
                        {item.resource.title} · {item.resource.level} · {item.recommend_score.toFixed(0)}점
                      </a>
                    ))}
                  </article>
                ))}
              </section>

              <section className="result-panel">
                <h3>주차별 학습 로드맵</h3>
                {result.weekly_roadmap.map((week) => (
                  <article key={week.week} className="roadmap-week">
                    <strong>{week.week}주차 · {week.goal}</strong>
                    <p>{week.practice}</p>
                  </article>
                ))}
              </section>

              <section className="result-panel">
                <h3>분석 리포트</h3>
                <p>{result.report}</p>
              </section>
            </>
          ) : (
            <p className="empty-state">채용공고와 지원 자료를 입력하면 분석 결과가 여기에 표시됩니다.</p>
          )}
        </section>
      </div>
    </main>
  );
}
```

- [ ] **Step 7: Run build**

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 8: Commit**

```bash
git add frontend/app/page.tsx frontend/lib/api.ts frontend/lib/types.ts frontend/components
git commit -m "Build user-centered analysis input flow"
```

---

## Task 8: Product Evaluation

**Files:**
- Create: `backend/tools/audit_learning_resources.py`
- Create: `backend/tools/evaluate_recommendations.py`
- Create: `backend/tools/write_evaluation_results.py`
- Create: `docs/evaluation-results.md`

- [ ] **Step 1: Add DB audit**

Create `backend/tools/audit_learning_resources.py`:

```python
from __future__ import annotations

from collections import Counter

from app.services.resource_loader import load_resources


REQUIRED_JOB_GROUPS = {"데이터 분석가", "AI/ML 엔지니어", "백엔드 개발자", "프론트엔드 개발자"}


def main() -> None:
    resources = load_resources()
    urls = [resource.url for resource in resources]
    job_counts = Counter(resource.job_group for resource in resources)
    duplicate_urls = [url for url, count in Counter(urls).items() if count > 1]
    invalid_reliability = [
        resource.id for resource in resources if resource.reliability < 1 or resource.reliability > 5
    ]

    print(f"resource_count={len(resources)}")
    print(f"job_group_counts={dict(sorted(job_counts.items()))}")
    print(f"duplicate_url_count={len(duplicate_urls)}")
    print(f"invalid_reliability_count={len(invalid_reliability)}")

    if len(resources) < 80:
        raise SystemExit("FAIL: learning resource DB must contain at least 80 rows")
    missing_groups = REQUIRED_JOB_GROUPS - set(job_counts)
    if missing_groups:
        raise SystemExit(f"FAIL: missing job groups: {sorted(missing_groups)}")
    if duplicate_urls:
        raise SystemExit(f"FAIL: duplicate URLs found: {duplicate_urls[:5]}")
    if invalid_reliability:
        raise SystemExit(f"FAIL: invalid reliability rows: {invalid_reliability[:5]}")

    print("audit_status=PASS")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add recommendation evaluator**

Create `backend/tools/evaluate_recommendations.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from app.services.resource_loader import load_resources
from app.services.retriever import TfidfRetriever
from app.services.scorer import difficulty_match, score_resource


@dataclass(frozen=True)
class BenchmarkCase:
    predicted_job: str
    skill: str
    difficulty: str
    query: str


BENCHMARKS = [
    BenchmarkCase("백엔드 개발자", "Docker", "입문", "백엔드 Docker 컨테이너 배포 입문"),
    BenchmarkCase("백엔드 개발자", "AWS", "기초", "백엔드 AWS 클라우드 배포 학습"),
    BenchmarkCase("프론트엔드 개발자", "React", "기초", "React 프론트엔드 컴포넌트 상태관리"),
    BenchmarkCase("프론트엔드 개발자", "TypeScript", "입문", "TypeScript JavaScript 타입 안정성"),
    BenchmarkCase("데이터 분석가", "SQL", "입문", "데이터 분석 SQL 쿼리 집계"),
    BenchmarkCase("데이터 분석가", "A/B 테스트", "기초", "A/B 테스트 통계 가설검정"),
    BenchmarkCase("AI/ML 엔지니어", "PyTorch", "기초", "PyTorch 딥러닝 모델 학습"),
    BenchmarkCase("AI/ML 엔지니어", "RAG", "실무", "LLM RAG 검색 증강 생성 파이프라인"),
]


def main() -> None:
    resources = load_resources()
    retriever = TfidfRetriever(resources)
    hit_count = 0
    precision_total = 0.0
    difficulty_total = 0.0

    for case in BENCHMARKS:
        candidates = retriever.search(case.query, limit=8)
        scored = [
            score_resource(
                resource=resource,
                semantic_similarity=similarity,
                skill=case.skill,
                predicted_job=case.predicted_job,
                user_difficulty=case.difficulty,
            )
            for resource, similarity in candidates
        ]
        top3 = sorted(scored, key=lambda item: item.recommend_score, reverse=True)[:3]
        skill_matches = [item for item in top3 if item.skill_match > 0]
        difficulty_matches = [
            item for item in top3 if difficulty_match(case.difficulty, item.resource) >= 0.5
        ]

        hit_count += 1 if skill_matches else 0
        precision_total += len(skill_matches) / 3
        difficulty_total += len(difficulty_matches) / 3

    case_count = len(BENCHMARKS)
    print(f"case_count={case_count}")
    print(f"hit_at_3={hit_count / case_count:.3f}")
    print(f"precision_at_3={precision_total / case_count:.3f}")
    print(f"difficulty_match_rate={difficulty_total / case_count:.3f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all checks**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py
PYTHONPATH=backend .venv/bin/python backend/tools/evaluate_recommendations.py
cd frontend && npm run build
```

Expected: tests and build pass. Metrics are printed from actual scripts.

- [ ] **Step 4: Document results**

Create `backend/tools/write_evaluation_results.py`:

```python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "evaluation-results.md"

COMMANDS = [
    (
        "Backend Tests",
        [sys.executable, "-m", "unittest", "discover", "-s", "backend/tests"],
        ROOT,
    ),
    (
        "Learning Resource DB Audit",
        [sys.executable, "backend/tools/audit_learning_resources.py"],
        ROOT,
    ),
    (
        "Recommendation Metrics",
        [sys.executable, "backend/tools/evaluate_recommendations.py"],
        ROOT,
    ),
    (
        "Frontend Build",
        ["npm", "run", "build"],
        ROOT / "frontend",
    ),
]


def run_command(title: str, command: list[str], cwd: Path) -> tuple[str, int]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "backend"
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    command_text = " ".join(command)
    section = "\n".join(
        [
            f"## {title}",
            "",
            f"Command: `{command_text}`",
            "",
            f"Exit code: `{result.returncode}`",
            "",
            "```text",
            output,
            "```",
            "",
        ]
    )
    return section, result.returncode


def main() -> None:
    sections = [
        "# Evaluation Results",
        "",
        "Generated: 2026-05-21",
        "",
    ]
    failed = False
    for title, command, cwd in COMMANDS:
        section, returncode = run_command(title, command, cwd)
        sections.append(section)
        if returncode != 0:
            failed = True

    OUTPUT.write_text("\n".join(sections), encoding="utf-8")
    print(f"wrote={OUTPUT}")
    if failed:
        raise SystemExit("FAIL: one or more evaluation commands failed")


if __name__ == "__main__":
    main()
```

Run:

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/write_evaluation_results.py
```

Expected: `docs/evaluation-results.md` is created with exact command output sections and the script exits with code 0.

- [ ] **Step 5: Commit**

```bash
git add backend/tools/audit_learning_resources.py backend/tools/evaluate_recommendations.py backend/tools/write_evaluation_results.py docs/evaluation-results.md
git commit -m "Add product evaluation metrics"
```

---

## Implementation Order

1. Product schemas.
2. Text extraction.
3. Skill analysis service.
4. Difficulty-aware recommendation scoring.
5. Weekly roadmap generation.
6. `/analyze` integration.
7. Frontend product input flow.
8. Product evaluation.

## Self-Review

- Covers user inputs: job posting, candidate materials, roadmap duration, difficulty, intensity.
- Covers outputs: predicted job, fit score, required skills, owned skills, missing skills, weekly roadmap, report.
- Removes internal role language from the product plan.
- Includes real evaluation metrics and forbids invented values.
