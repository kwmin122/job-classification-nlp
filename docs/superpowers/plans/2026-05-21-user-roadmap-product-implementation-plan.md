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

from app.schemas import AnalyzeRequest, RoadmapPreferences


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
        self.assertTrue(body["missing_skills"])
        self.assertTrue(body["weekly_roadmap"])
```

- [ ] **Step 2: Run failing test**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_analyze_api.py
```

Expected: fails because `/analyze` does not exist.

- [ ] **Step 3: Implement endpoint**

Implement the endpoint by:

1. Extracting job text.
2. Combining candidate material text.
3. Running skill analysis.
4. Running resource recommendation for missing skills.
5. Generating weekly roadmap.
6. Returning product response.

- [ ] **Step 4: Verify**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_analyze_api.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_analyze_api.py
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
export type RoadmapPreferences = {
  duration_weeks: 2 | 4 | 8 | 12;
  difficulty: "입문" | "기초" | "실무" | "심화";
  intensity: "가볍게" | "보통" | "집중";
};
```

- [ ] **Step 2: Add API client**

```ts
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

- [ ] **Step 3: Replace primary UI**

The first screen must show:

- `지원할 채용공고`
- `내 지원 자료`
- `학습 목표`
- `분석 시작`

- [ ] **Step 4: Run build**

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 5: Commit**

```bash
git add frontend/app/page.tsx frontend/lib/api.ts frontend/lib/types.ts frontend/components
git commit -m "Build user-centered analysis input flow"
```

---

## Task 8: Product Evaluation

**Files:**
- Create: `backend/tools/audit_learning_resources.py`
- Create: `backend/tools/evaluate_recommendations.py`
- Create: `docs/evaluation-results.md`

- [ ] **Step 1: Add DB audit**

Audit row count, job group coverage, reliability range, and duplicate URLs.

- [ ] **Step 2: Add recommendation evaluator**

Calculate:

- Hit@3
- Precision@3
- difficulty match rate

- [ ] **Step 3: Run all checks**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py
PYTHONPATH=backend .venv/bin/python backend/tools/evaluate_recommendations.py
cd frontend && npm run build
```

Expected: tests and build pass. Metrics are printed from actual scripts.

- [ ] **Step 4: Document results**

Create `docs/evaluation-results.md` and paste the exact command outputs used for the final run.

- [ ] **Step 5: Commit**

```bash
git add backend/tools/audit_learning_resources.py backend/tools/evaluate_recommendations.py docs/evaluation-results.md
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
