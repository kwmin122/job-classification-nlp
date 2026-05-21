# Design

## Design System Overview

The interface is a local product dashboard for job-posting skill-gap analysis and personalized learning-roadmap recommendation. It should support the real user flow: enter a job posting, enter candidate materials, choose roadmap constraints, run analysis, review gaps, then study the recommended roadmap.

## Color

Use OKLCH colors through CSS custom properties.

- Background: warm-tinted neutral, not pure white.
- Surface: slightly raised neutral panels with low-contrast borders.
- Text: ink-like neutral, not pure black.
- Primary accent: deep teal for the main analysis action and top-priority skill.
- Secondary accents: muted amber for medium gaps, muted red for high gaps, muted green for satisfied skills, slate-blue for method metadata.

## Typography

Use a system UI stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`.

- Page title: 28px, 700 weight.
- Section title: 16px to 18px, 700 weight.
- Body: 14px to 15px.
- Labels and metadata: 12px to 13px.
- Data numbers: tabular numerals.

## Layout

The primary layout is a product work surface:

- Input area: job posting source, candidate material source, roadmap preferences.
- Analysis summary: predicted job, fit score, number of missing skills, top priority.
- Evidence area: required skills, owned skills, missing skills, score bars, evidence sentences.
- Recommendation area: learning resources grouped by missing skill.
- Roadmap area: week-by-week learning plan.
- Report area: natural-language summary and method disclosure.

The input area must start from the user's real job target and candidate materials. Any internal diagnostics should stay outside the normal product flow.

## Input Components

- Job posting URL field.
- Job posting text area.
- Job posting PDF/TXT upload.
- Candidate material text area.
- Candidate PDF/TXT upload.
- Optional portfolio/GitHub README text area.
- Roadmap duration segmented control: 2주, 4주, 8주, 12주.
- Current level segmented control: 입문, 기초, 실무, 심화.
- Learning intensity segmented control: 가볍게, 보통, 집중.
- Primary button: `분석 시작`.

Demo-data controls are not part of the real user flow. If seeded data is needed for development, keep it outside the primary UI.

## Result Components

- Summary strip: predicted job, fit score, missing skill count, top priority.
- Required skills panel: requirement, importance, job-posting evidence.
- Owned skills panel: skill, candidate evidence.
- Gap matrix: skill, gap score, level, importance, missing reason.
- Resource recommendation rows: title, type, level, language, reliability, recommend score, reason, URL.
- Weekly roadmap timeline: week number, goal, skills, resources, practice output.
- Report panel: generated Korean summary with clear caveats.
- Method panel: retrieval mode, embedding model, scoring formula, RAG scope.

## Interaction

- The user should be able to paste text or upload files without understanding backend contracts.
- The roadmap preferences should be visible before analysis because they affect the recommendation.
- Loading should clearly indicate whether the app is extracting text, analyzing gaps, retrieving resources, or generating the roadmap.
- Errors should say what failed: URL extraction, file parsing, insufficient text, analysis failure, or recommendation failure.
- The app should keep the user’s pasted text if an error occurs.

## Motion

Use short 150-220ms transitions for hover, focus, panel reveal, and score bars. Avoid decorative page-load choreography. Respect `prefers-reduced-motion`.

## Content

Labels are Korean-first. Technical terms like RAG, gap score, embedding, and Top-K may appear only in method disclosure areas. Primary headings should use user-facing language such as `채용공고 분석`, `내 지원 자료`, `학습 목표`, `보완 필요 역량`, and `주차별 학습 로드맵`.
