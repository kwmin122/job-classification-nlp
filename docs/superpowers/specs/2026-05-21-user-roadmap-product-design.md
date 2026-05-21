# User Roadmap Product Design

Generated: 2026-05-21
Status: Approved user-centered product design

## Goal

Build a product where a job seeker submits a target job posting and their own application materials, chooses a learning timeline and difficulty level, and receives skill-gap analysis plus a personalized weekly learning roadmap.

## User Story

As a job seeker, I want to compare my cover letter, resume, and portfolio against a job posting, so that I can understand what skills I am missing and what to study before applying.

## Inputs

- Job posting URL.
- Job posting pasted text.
- Job posting PDF/TXT upload.
- Candidate cover letter, resume, portfolio, or GitHub README text.
- Candidate PDF/TXT upload.
- Roadmap duration: 2, 4, 8, or 12 weeks.
- Current level: 입문, 기초, 실무, 심화.
- Learning intensity: 가볍게, 보통, 집중.

## Outputs

- Predicted job group.
- Fit score.
- Required skills with evidence from the job posting.
- Owned skills with evidence from candidate materials.
- Missing skills with gap score, level, importance, and evidence.
- Recommended learning resources.
- Weekly roadmap.
- Practice project suggestions.
- Natural-language report.

## Product Flow

```text
User enters target job posting
User enters candidate materials
User chooses roadmap preferences
        ↓
System extracts and cleans text
        ↓
System classifies job group
        ↓
System extracts required and owned skills
        ↓
System calculates missing skills and gap scores
        ↓
System searches curated learning resources
        ↓
System ranks resources with difficulty preference
        ↓
System builds weekly roadmap
        ↓
System displays report and evidence
```

## UI Sections

1. `지원할 채용공고`
   - URL input
   - Textarea
   - PDF/TXT upload

2. `내 지원 자료`
   - Cover letter/resume/portfolio textarea
   - PDF/TXT upload
   - Optional GitHub README text

3. `학습 목표`
   - Duration segmented control
   - Current level segmented control
   - Intensity segmented control

4. `분석 결과`
   - Predicted job
   - Fit score
   - Missing skill count
   - Top priority skill

5. `근거 기반 격차 분석`
   - Required skills
   - Owned skills
   - Missing skills
   - Evidence sentences

6. `주차별 학습 로드맵`
   - Week number
   - Goal
   - Resources
   - Practice output

7. `추천 자료`
   - Resource title
   - Type
   - Level
   - Reliability
   - Recommendation reason

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
  ],
  "roadmap_preferences": {
    "duration_weeks": 4,
    "difficulty": "입문",
    "intensity": "보통"
  }
}
```

### Response

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 78,
  "required_skills": [],
  "owned_skills": [],
  "missing_skills": [],
  "recommended_resources": [],
  "weekly_roadmap": [],
  "report": ""
}
```

## Error Handling

- URL extraction failed: ask the user to paste the job posting text.
- File parsing failed: show file type and parsing error.
- Candidate text too short: ask for more content.
- No missing skills found: show matched skills and explain that recommendations may be limited.
- Recommendation retrieval failed: show the gap analysis and allow retrying resource recommendation.

## Verification

- User can submit job posting text and candidate text and receive a full result.
- User can choose 2, 4, 8, or 12 weeks and see the roadmap length change.
- User can choose difficulty and see recommended resource levels shift.
- Result includes evidence for missing skills.
- Recommendation section uses `learning_resources.csv`.
- Method disclosure states curated resource DB retrieval, not open-web search.
