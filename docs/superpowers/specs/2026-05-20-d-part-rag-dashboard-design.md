# D Part RAG Dashboard Design

## Goal

Implement the D-part vertical slice for the NLP final project:

```text
C output JSON
→ curated learning-resource DB retrieval
→ ranked recommendations
→ gap-based learning roadmap
→ template report
→ local dashboard
```

This slice proves the D role end to end without waiting for the final C module. C's result is represented by `sample_c_output.json`.

## Scope

### In Scope

- Curated learning-resource DB with at least 80 rows.
- Mixed source policy: official docs first, plus popular YouTube, blog, course, and practice-platform resources when they are useful for beginners or project work.
- Local retrieval over `learning_resources.csv`.
- Recommendation score normalized to 0-100.
- Gap-score-aware roadmap generation.
- Template-based Korean report generation.
- Local dashboard using Next.js.
- Python backend API serving the recommendation pipeline.
- README with honest RAG explanation and run commands.

### Out of Scope

- Open-web crawling.
- Paid LLM API dependency.
- Training a new model.
- Computing the original gap score from raw JD/resume text.
- Production authentication or deployment.

## Architecture

Use a split local app:

- `backend`: Python API and RAG/recommendation logic.
- `frontend`: Next.js dashboard.

The backend remains the source of truth for D-part logic. The frontend presents the output and helps the presenter explain it.

## C to D Input Contract

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 72,
  "matched_skills": ["Java", "Spring Boot", "MySQL"],
  "skill_gaps": [
    {
      "skill": "Docker",
      "gap_score": 82,
      "gap_level": "높음",
      "importance": "필수",
      "evidence": "JD에는 Docker 배포 경험이 요구되지만 지원자 텍스트에는 관련 경험이 없음"
    }
  ]
}
```

D does not recalculate the missing skills. It consumes this contract and turns it into recommendations.

## Learning Resource DB Schema

`backend/app/data/learning_resources.csv`

| Field | Purpose |
|---|---|
| id | Stable row id |
| job_group | Target job group |
| skill | Main skill |
| sub_skill | More specific topic |
| title | Resource title |
| description | Searchable description |
| url | Source URL |
| type | 공식문서, 유튜브, 블로그, 책, 실습플랫폼, 강의 |
| level | beginner, intermediate, advanced |
| language | 한국어 or 영어 |
| free_or_paid | 무료, 유료, 부분무료 |
| estimated_time | Rough study duration |
| reliability | Integer 1-5 |
| reason | Why this resource is useful |

## Recommendation Formula

```text
recommend_score =
100 * (
  0.6 * semantic_similarity
+ 0.2 * skill_match
+ 0.1 * job_group_match
+ 0.1 * reliability_norm
)
```

Normalization:

- `semantic_similarity`: 0-1.
- `skill_match`: 0 or 1.
- `job_group_match`: 0 or 1.
- `reliability_norm`: `reliability / 5`.

For the stable vertical slice, `semantic_similarity` uses a local TF-IDF cosine retriever. The code keeps the service boundary clear so Sentence-BERT can replace it later.

## Honest RAG Definition

This is not open-web RAG. It is a curated learning-resource DB retrieval pipeline. The DB intentionally mixes source types, but source quality is explicit through `type` and `reliability`.

```text
부족 역량
→ learning_resources.csv 검색
→ 관련 자료 Top-K 추출
→ 로드맵과 리포트 생성
```

Source policy:

- Official documentation or official learning pages usually receive reliability 5.
- Popular practice platforms, reputable tutorials, and education sites usually receive reliability 4.
- Popular YouTube channels are useful for entry and intuition, but receive reliability 3-4 depending on scope.
- Every URL must pass `backend/tools/verify_resource_urls.py`.

## Dashboard Design

The dashboard is a local analysis work surface, not a marketing page.

- Left rail: JSON input, sample controls, pipeline note.
- Summary strip: predicted job, fit score, gap count, top priority.
- Gap matrix: skill, importance, gap score bar, level, evidence.
- Recommendation area: grouped by skill with Top-K resources.
- Roadmap: ordered steps and practice project.
- Report: Korean natural-language explanation.

## States

- Default with sample ready.
- Loading while recommendation request runs.
- Error for invalid JSON or backend failure.
- Empty result if no skill gaps exist.
- Responsive layout for desktop and narrow screens.

## Verification

- Backend health endpoint returns OK.
- Backend recommendation endpoint returns resource recommendations for sample input.
- Frontend build passes.
- Local dashboard can call backend successfully.
- Browser inspection confirms no obvious overflow or blank states on desktop and mobile widths.
