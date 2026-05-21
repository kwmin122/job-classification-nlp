# D RAG Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build D's final deliverable: consume C's skill-gap analysis, retrieve learning resources from the curated DB, generate recommendations, roadmap, report, evaluation metrics, and integrate the final result dashboard.

**Architecture:** A/B/C own raw data collection, preprocessing, job classification, skill extraction, and gap scoring. D owns the downstream recommendation pipeline plus the user-facing result/dashboard integration. The final product UI starts from raw job posting and candidate materials, but D's backend boundary starts from an agreed `AnalysisResult` contract produced by C.

**Tech Stack:** FastAPI, Pydantic, CSV resource DB, OpenAI `text-embedding-3-small` with TF-IDF fallback, NumPy cosine similarity, Next.js local dashboard, Python unittest, URL validation script.

---

## Scope Boundary

D does:

- Maintain `learning_resources.csv` with 80+ curated resources.
- Validate resource quality, coverage, URL availability, and source reliability.
- Consume C's `AnalysisResult` containing predicted job, fit score, required skills, owned skills, missing skills, gap scores, and evidence.
- Search the learning-resource DB for each missing skill.
- Score and rank recommended resources.
- Generate a prioritized learning roadmap.
- Generate a natural-language report from computed facts only.
- Integrate the final dashboard with the full product flow.
- Produce actual D-side evaluation metrics.

D does not:

- Crawl all job postings.
- Train the job classifier.
- Compute final job-classification Accuracy/F1.
- Decide missing skills from raw text by itself.
- Invent candidate experience in the report.

## Files

- Modify: `backend/app/schemas.py`
  - Add the final C-to-D contract types: required skills, owned skills, gap analysis, analysis response.
- Modify: `backend/app/main.py`
  - Keep `/recommend` as D-only contract endpoint.
  - Add `/analyze` integration request and response shape for full product flow.
- Modify: `backend/app/services/resource_loader.py`
  - Keep resource loading and expose row-count and coverage helpers for audits.
- Modify: `backend/app/services/embedding_retriever.py`
  - Ensure OpenAI embedding retriever and TF-IDF fallback expose metadata.
- Modify: `backend/app/services/scorer.py`
  - Keep recommendation formula and expose score components.
- Modify: `backend/app/services/roadmap_generator.py`
  - Improve roadmap generation using gap level, skill type, resource level, and evidence.
- Modify: `backend/app/services/report_generator.py`
  - Make report product-facing and fact-grounded.
- Create: `backend/tools/evaluate_recommendations.py`
  - Calculate D-side retrieval and recommendation metrics.
- Create: `backend/app/data/eval_gap_cases.csv`
  - Small labeled evaluation set for recommendation relevance.
- Modify: `frontend/app/page.tsx`
  - Replace developer payload input with product input flow or connect to the final `/analyze` result.
- Modify: `frontend/components/GapMatrix.tsx`
  - Show gap score, level, importance, and evidence.
- Modify: `frontend/components/ResourceRecommendations.tsx`
  - Show resource score components and source metadata.
- Modify: `frontend/components/RoadmapPanel.tsx`
  - Show prioritized learning stages and practice project.
- Modify: `frontend/components/ReportPanel.tsx`
  - Show grounded report and method disclosure.
- Create: `frontend/components/JobPostingInputPanel.tsx`
  - Job posting URL/text/file input controls.
- Create: `frontend/components/CandidateInputPanel.tsx`
  - Candidate cover letter/resume/portfolio input controls.
- Modify: `README.md`
  - Add D execution and evaluation commands after implementation.

---

## Task 1: Lock the C-to-D Contract

**Files:**
- Modify: `backend/app/schemas.py`
- Test: `backend/tests/test_recommend_api.py`

- [ ] **Step 1: Define the contract**

Add schema types so C can pass richer analysis results to D.

```python
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


class SkillGap(BaseModel):
    skill: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    evidence: str


class AnalysisResult(BaseModel):
    predicted_job: str
    fit_score: float = Field(ge=0, le=100)
    required_skills: list[RequiredSkill] = Field(default_factory=list)
    owned_skills: list[OwnedSkill] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[SkillGap]
```

- [ ] **Step 2: Keep backwards compatibility**

Keep `COutput` as an alias or compatible model for the current `/recommend` endpoint.

```python
class COutput(AnalysisResult):
    pass
```

- [ ] **Step 3: Add API contract test**

Add a test that posts an `AnalysisResult` with required and owned skills to `/recommend`.

```python
def test_recommend_accepts_full_analysis_result(self) -> None:
    client = TestClient(app)
    payload = {
        "predicted_job": "백엔드 개발자",
        "fit_score": 72,
        "required_skills": [
            {
                "skill": "Docker",
                "importance": "필수",
                "evidence": [{"text": "Docker 기반 배포 경험", "source": "job_posting"}],
            }
        ],
        "owned_skills": [
            {
                "skill": "Spring Boot",
                "evidence": [{"text": "Spring Boot API 개발", "source": "candidate"}],
            }
        ],
        "matched_skills": ["Spring Boot"],
        "skill_gaps": [
            {
                "skill": "Docker",
                "gap_score": 82,
                "gap_level": "높음",
                "importance": "필수",
                "evidence": "지원자 자료에 Docker 배포 경험이 명확히 나타나지 않음",
            }
        ],
    }
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    assert response.json()["top_priority_skill"] == "Docker"
```

- [ ] **Step 4: Verify**

Run:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_recommend_api.py
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas.py backend/tests/test_recommend_api.py
git commit -m "Define analysis result contract for D pipeline"
```

---

## Task 2: Resource DB Quality Gate

**Files:**
- Create: `backend/tools/audit_learning_resources.py`
- Modify: `README.md`

- [ ] **Step 1: Add audit script**

Create a script that checks row count, required columns, job-group coverage, skill coverage, reliability range, and duplicate URLs.

```python
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

RESOURCE_PATH = Path("backend/app/data/learning_resources.csv")
REQUIRED_COLUMNS = {
    "id",
    "job_group",
    "skill",
    "sub_skill",
    "title",
    "description",
    "url",
    "type",
    "level",
    "language",
    "free_or_paid",
    "estimated_time",
    "reliability",
    "reason",
}


def main() -> int:
    with RESOURCE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    missing_columns = REQUIRED_COLUMNS - set(rows[0].keys())
    errors: list[str] = []
    if missing_columns:
        errors.append(f"missing columns: {sorted(missing_columns)}")
    if len(rows) < 80:
        errors.append(f"expected at least 80 rows, got {len(rows)}")

    job_counts = Counter(row["job_group"] for row in rows)
    for job_group in ["데이터 분석가", "AI/ML 엔지니어", "백엔드 개발자", "프론트엔드 개발자"]:
        if job_counts[job_group] < 20:
            errors.append(f"{job_group} has {job_counts[job_group]} rows, expected >= 20")

    urls = [row["url"] for row in rows]
    duplicate_urls = [url for url, count in Counter(urls).items() if count > 1]
    if duplicate_urls:
        errors.append(f"duplicate urls: {duplicate_urls[:10]}")

    for row in rows:
        reliability = int(row["reliability"])
        if reliability < 1 or reliability > 5:
            errors.append(f"{row['id']} reliability out of range: {reliability}")

    print(f"resource_count={len(rows)}")
    print(f"job_group_counts={dict(job_counts)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("resource_audit=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run audit**

Run:

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py
```

Expected: `resource_audit=pass`.

- [ ] **Step 3: Run URL validation**

Run:

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/verify_resource_urls.py
```

Expected: no failed URLs.

- [ ] **Step 4: Commit**

```bash
git add backend/tools/audit_learning_resources.py README.md
git commit -m "Add learning resource DB quality audit"
```

---

## Task 3: Recommendation Evaluation Metrics

**Files:**
- Create: `backend/app/data/eval_gap_cases.csv`
- Create: `backend/tools/evaluate_recommendations.py`
- Test: `backend/tests/test_recommendation_evaluation.py`

- [ ] **Step 1: Add evaluation dataset**

Create `backend/app/data/eval_gap_cases.csv`.

```csv
case_id,predicted_job,skill,gap_score,gap_level,importance,evidence,expected_resource_ids
BE_DOCKER,백엔드 개발자,Docker,82,높음,필수,Docker 기반 배포 경험이 부족함,"BE009;BE012;BE020"
BE_CICD,백엔드 개발자,CI/CD,76,높음,필수,배포 자동화 경험이 확인되지 않음,"BE011;BE012;BE019"
BE_AWS,백엔드 개발자,AWS,64,중간,우대,클라우드 배포 경험이 구체적으로 드러나지 않음,"BE007;BE008;DA015"
DA_SQL,데이터 분석가,SQL,70,높음,필수,SQL 분석 경험이 부족함,"DA003;DA004"
FE_REACT,프론트엔드 개발자,React,78,높음,필수,React 프로젝트 경험이 부족함,"FE005;FE006"
AI_PYTORCH,AI/ML 엔지니어,PyTorch,72,높음,필수,딥러닝 프레임워크 경험이 부족함,"AI005;AI006"
```

- [ ] **Step 2: Add evaluator script**

```python
from __future__ import annotations

import csv
from pathlib import Path

from app.main import recommend
from app.schemas import COutput, SkillGap

EVAL_PATH = Path("backend/app/data/eval_gap_cases.csv")


def hit_at_k(actual_ids: list[str], expected_ids: set[str], k: int) -> float:
    return 1.0 if expected_ids.intersection(actual_ids[:k]) else 0.0


def precision_at_k(actual_ids: list[str], expected_ids: set[str], k: int) -> float:
    if k == 0:
        return 0.0
    return sum(1 for resource_id in actual_ids[:k] if resource_id in expected_ids) / k


def main() -> int:
    with EVAL_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    hit_scores: list[float] = []
    precision_scores: list[float] = []

    for row in rows:
        payload = COutput(
            predicted_job=row["predicted_job"],
            fit_score=70,
            matched_skills=[],
            skill_gaps=[
                SkillGap(
                    skill=row["skill"],
                    gap_score=float(row["gap_score"]),
                    gap_level=row["gap_level"],
                    importance=row["importance"],
                    evidence=row["evidence"],
                )
            ],
        )
        response = recommend(payload, top_k=3)
        actual_ids = [
            item.resource.id
            for item in response.skill_recommendations[0].recommendations
        ]
        expected_ids = set(row["expected_resource_ids"].split(";"))
        hit_scores.append(hit_at_k(actual_ids, expected_ids, 3))
        precision_scores.append(precision_at_k(actual_ids, expected_ids, 3))
        print(
            f"{row['case_id']}: actual={actual_ids} expected={sorted(expected_ids)}"
        )

    hit_rate = sum(hit_scores) / len(hit_scores)
    precision = sum(precision_scores) / len(precision_scores)
    print(f"hit@3={hit_rate:.3f}")
    print(f"precision@3={precision:.3f}")
    return 0 if hit_rate >= 0.80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Add evaluator unit test**

```python
from backend.tools.evaluate_recommendations import hit_at_k, precision_at_k


def test_hit_at_k_detects_expected_resource() -> None:
    assert hit_at_k(["A", "B", "C"], {"C"}, 3) == 1.0
    assert hit_at_k(["A", "B", "C"], {"D"}, 3) == 0.0


def test_precision_at_k_counts_relevant_items() -> None:
    assert precision_at_k(["A", "B", "C"], {"A", "C"}, 3) == 2 / 3
```

- [ ] **Step 4: Run evaluator**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m unittest backend/tests/test_recommendation_evaluation.py
PYTHONPATH=backend .venv/bin/python backend/tools/evaluate_recommendations.py
```

Expected: unit test passes, evaluator prints `hit@3` and `precision@3`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/data/eval_gap_cases.csv backend/tools/evaluate_recommendations.py backend/tests/test_recommendation_evaluation.py
git commit -m "Add D-side recommendation evaluation"
```

---

## Task 4: Roadmap Generator Upgrade

**Files:**
- Modify: `backend/app/services/roadmap_generator.py`
- Test: `backend/tests/test_roadmap_generator.py`

- [ ] **Step 1: Write roadmap tests**

```python
import unittest

from app.schemas import Resource, ResourceRecommendation, SkillRecommendation
from app.services.roadmap_generator import generate_roadmap


def resource(resource_id: str, title: str, level: str = "beginner") -> Resource:
    return Resource(
        id=resource_id,
        job_group="백엔드 개발자",
        skill="Docker",
        sub_skill="컨테이너",
        title=title,
        description="Docker 학습",
        url="https://example.com",
        type="공식문서",
        level=level,
        language="한국어",
        free_or_paid="무료",
        estimated_time="3시간",
        reliability=5,
        reason="Docker 배포 경험 보완",
    )


class RoadmapGeneratorTest(unittest.TestCase):
    def test_high_gap_roadmap_starts_with_foundation_and_project(self) -> None:
        recommendation = ResourceRecommendation(
            resource=resource("BE009", "Docker 입문"),
            semantic_similarity=0.9,
            skill_match=1,
            job_group_match=1,
            reliability_norm=1,
            recommend_score=94,
        )
        item = SkillRecommendation(
            skill="Docker",
            gap_score=82,
            gap_level="높음",
            importance="필수",
            evidence="Docker 배포 경험이 부족함",
            query="백엔드 Docker",
            recommendations=[recommendation],
        )
        roadmap = generate_roadmap([item])
        self.assertEqual(roadmap[0].priority, 1)
        self.assertIn("Docker", roadmap[0].steps[0])
        self.assertIn("포트폴리오", roadmap[0].steps[-1])
```

- [ ] **Step 2: Improve roadmap generation**

Adjust generation so roadmap content uses:

- gap score
- importance
- top resource titles
- practice project
- evidence wording

Keep the implementation deterministic and template-based.

- [ ] **Step 3: Run tests**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_roadmap_generator.py
```

Expected: tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/roadmap_generator.py backend/tests/test_roadmap_generator.py
git commit -m "Improve gap-aware roadmap generation"
```

---

## Task 5: Report Generator and Prompting Guardrails

**Files:**
- Modify: `backend/app/services/report_generator.py`
- Create: `backend/app/prompts/report_prompt.txt`
- Test: `backend/tests/test_report_generator.py`

- [ ] **Step 1: Add report prompt file**

```text
너는 취업 역량 분석 리포트 작성 도우미다.

규칙:
1. 제공된 분석 결과와 추천 자료만 사용한다.
2. 지원자에게 없는 경험을 지어내지 않는다.
3. 부족 역량, gap_score, 근거 문장을 명확히 설명한다.
4. 추천 자료는 학습자료 DB에서 검색된 자료만 언급한다.
5. 웹 전체 검색 결과처럼 표현하지 않는다.

출력:
1. 전체 요약
2. 우선 보완 역량
3. 추천 학습 순서
4. 실습 프로젝트
5. 한계와 주의점
```

- [ ] **Step 2: Add report tests**

```python
import unittest

from app.schemas import COutput, SkillGap
from app.services.report_generator import generate_report


class ReportGeneratorTest(unittest.TestCase):
    def test_report_does_not_claim_unprovided_experience(self) -> None:
        c_output = COutput(
            predicted_job="백엔드 개발자",
            fit_score=72,
            matched_skills=["Spring Boot"],
            skill_gaps=[
                SkillGap(
                    skill="Docker",
                    gap_score=82,
                    gap_level="높음",
                    importance="필수",
                    evidence="Docker 배포 경험이 명확히 나타나지 않음",
                )
            ],
        )
        report = generate_report(c_output, [], [])
        self.assertIn("Docker", report)
        self.assertNotIn("Docker 경험을 보유", report)
```

- [ ] **Step 3: Update report generator**

Ensure the report always includes:

- predicted job
- fit score
- top missing skill
- evidence
- recommendation source caveat
- limitation: this is based on input text and curated DB

- [ ] **Step 4: Run tests**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_report_generator.py
```

Expected: tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/report_generator.py backend/app/prompts/report_prompt.txt backend/tests/test_report_generator.py
git commit -m "Add grounded report generation guardrails"
```

---

## Task 6: Dashboard Integration for Final Product Flow

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/lib/types.ts`
- Create or modify: `frontend/components/JobPostingInputPanel.tsx`
- Create or modify: `frontend/components/CandidateInputPanel.tsx`
- Modify: `frontend/components/GapMatrix.tsx`
- Modify: `frontend/components/ResourceRecommendations.tsx`

- [ ] **Step 1: Define frontend request types**

Add types for the final input flow.

```ts
export type SourceType = "url" | "text" | "file";

export type JobPostingInput = {
  source_type: SourceType;
  url?: string;
  text?: string;
};

export type CandidateMaterialInput = {
  source_type: SourceType;
  label: string;
  text?: string;
};

export type AnalyzeRequest = {
  job_posting: JobPostingInput;
  candidate_materials: CandidateMaterialInput[];
};
```

- [ ] **Step 2: Add API client**

```ts
export async function analyze(payload: AnalyzeRequest): Promise<RecommendResponse> {
  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return parseResponse<RecommendResponse>(response);
}
```

- [ ] **Step 3: Replace primary JSON UI**

The main UI should show:

- `채용공고 URL`
- `채용공고 본문`
- `지원자 자소서/이력서/포트폴리오`
- `분석 시작`

Keep developer contract input out of the primary UI.

- [ ] **Step 4: Add progress labels**

Use deterministic states:

```ts
type AnalyzeStatus =
  | "idle"
  | "extracting"
  | "analyzing"
  | "retrieving"
  | "complete"
  | "error";
```

- [ ] **Step 5: Run frontend build**

```bash
cd frontend
npm run build
```

Expected: Next build passes.

- [ ] **Step 6: Commit**

```bash
git add frontend/app/page.tsx frontend/lib/api.ts frontend/lib/types.ts frontend/components
git commit -m "Integrate dashboard with real input analysis flow"
```

---

## Task 7: Full D Verification and Metrics Table

**Files:**
- Modify: `README.md`
- Create: `docs/d-evaluation-results.md`

- [ ] **Step 1: Run backend tests**

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
```

Expected: all tests pass.

- [ ] **Step 2: Run resource checks**

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py
PYTHONPATH=backend .venv/bin/python backend/tools/verify_resource_urls.py
```

Expected: DB audit passes and URLs are valid or documented.

- [ ] **Step 3: Run D recommendation evaluation**

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/evaluate_recommendations.py
```

Expected: prints actual `hit@3` and `precision@3`.

- [ ] **Step 4: Run frontend build**

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 5: Write evaluation results doc from command output**

Create `docs/d-evaluation-results.md`.

```markdown
# D 파트 평가 결과

Generated: 2026-05-21

## Resource DB

Paste the exact `audit_learning_resources.py` and `verify_resource_urls.py` output used for the final run.

## Recommendation Retrieval

Paste the exact `evaluate_recommendations.py` output used for the final run.

## Notes

- 평가 수치는 위 스크립트 출력에 나온 값만 기록한다.
- 실패 URL이나 낮은 추천 정확도는 숨기지 않고 개선 항목으로 기록한다.
```

- [ ] **Step 6: Commit**

```bash
git add README.md docs/d-evaluation-results.md
git commit -m "Document D evaluation results"
```

---

## Implementation Order

1. Contract first: C-to-D schema.
2. Resource DB quality gate.
3. Recommendation evaluation metrics.
4. Roadmap and report quality.
5. Dashboard real-input integration.
6. Final verification and evaluation table.

This order keeps D independently testable even while A/B/C are still finishing their parts.

## Self-Review

- Spec coverage: covers D's DB, RAG, scoring, roadmap, report, dashboard, and evaluation metrics.
- Scope: does not assign job classification or gap-score calculation internals to D.
- Evaluation docs require actual script output, not invented values.
- Integration: defines C-to-D contract and final `/analyze` frontend connection.
