# Real Input Skill-Gap Roadmap Design

Generated: 2026-05-21  
Status: Design spec for the real-input product flow

## Goal

Build a final-product vertical slice where the user provides a target job posting and their own candidate materials. The system analyzes the raw inputs, identifies missing skills and gap scores, then recommends learning resources and a roadmap.

The product starts from real user-provided job posting and candidate materials.

## In Scope

- Job posting URL input.
- Job posting pasted text input.
- Job posting PDF/TXT upload.
- Candidate cover letter/resume/portfolio pasted text input.
- Candidate PDF/TXT upload.
- Text extraction and cleaning.
- Job group prediction.
- Required skill extraction.
- Owned skill extraction.
- Missing skill and gap score calculation.
- Curated learning-resource DB retrieval.
- Recommendation score calculation.
- Learning roadmap generation.
- Natural-language report generation.
- Local dashboard.

## Out of Scope for First Stable Slice

- DOCX/HWP parsing.
- Multi-file project archive ingestion.
- Login or account storage.
- Production deployment.
- Open-web learning-resource crawling.
- Claiming full market-wide skill statistics.

## Architecture

```text
frontend input form
        ↓
POST /analyze
        ↓
job posting text extraction
candidate text extraction
        ↓
job classifier
required skill extractor
owned skill extractor
        ↓
gap analyzer
        ↓
RAG resource retriever
        ↓
roadmap/report generator
        ↓
frontend dashboard
```

## API Contract

### Request

```json
{
  "job_posting": {
    "source_type": "url",
    "url": "https://example.com/job/123",
    "text": ""
  },
  "candidate_materials": [
    {
      "source_type": "text",
      "label": "자소서",
      "text": "지원자 자기소개서 본문"
    }
  ]
}
```

### Response

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 78,
  "required_skills": [],
  "owned_skills": [],
  "skill_gaps": [],
  "skill_recommendations": [],
  "roadmap": [],
  "report": ""
}
```

## UI Design

Primary user-facing areas:

1. `채용공고`: URL, text, or file.
2. `지원자 자료`: 자소서/이력서/포트폴리오 text or file.
3. `분석 시작`: runs extraction, gap analysis, and recommendation.
4. `분석 요약`: predicted job, fit score, missing skill count, top priority.
5. `역량 근거`: required skills, owned skills, missing skills, evidence.
6. `학습자료 추천`: resource rows grouped by missing skill.
7. `학습 로드맵`: ordered learning plan.
8. `분석 리포트`: readable Korean report and method disclosure.

The UI must not make a developer payload editor the default experience. Demo-data controls are not part of the real product flow.

## Error Handling

- URL extraction failed: ask the user to paste the job posting text.
- File parsing failed: show file type and parsing error.
- Candidate text too short: ask for more content.
- No missing skills found: show matched skills and explain that recommendations are limited.
- Recommendation retrieval failed: show gap analysis and retry recommendation separately.

## Verification

- User can paste a job posting and candidate text and receive a full result.
- User can upload PDF/TXT for at least one side of the input.
- No user-facing label exposes internal team roles or developer-only payload language.
- The response includes evidence for missing skills.
- The recommendation section uses `learning_resources.csv`.
- The method disclosure states that the system uses curated resource DB retrieval, not open-web search.
