# Design

## Design System Overview

The interface is a local product dashboard for job-posting skill-gap analysis and learning-roadmap recommendation. It should support a real user flow: enter a job posting, enter candidate materials, run analysis, review gaps, then study the recommended roadmap.

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

- Input area: job posting source and candidate material source.
- Analysis summary: predicted job, fit score, number of missing skills, top priority.
- Gap evidence: required skills, owned skills, missing skills, score bars, evidence sentences.
- Recommendation area: learning resources grouped by missing skill.
- Roadmap area: priority sequence and practice project.
- Report area: natural-language summary and method disclosure.

The input area must not be a developer payload contract as the default user experience. Diagnostics can be kept only as hidden debugging tools if needed.

## Input Components

- Job posting URL field.
- Job posting text area.
- Job posting PDF/TXT upload.
- Candidate material text area.
- Candidate PDF/TXT upload.
- Optional portfolio/GitHub README text area.
- Primary button: `분석 시작`.

Demo-data controls are not part of the real user flow. If seeded data is needed for development, keep it outside the primary UI.

## Result Components

- Summary strip: predicted job, fit score, missing skill count, top priority.
- Required skills panel: requirement, importance, job-posting evidence.
- Owned skills panel: skill, candidate evidence.
- Gap matrix: skill, gap score, level, importance, missing reason.
- Resource recommendation rows: title, type, level, language, reliability, recommend score, reason, URL.
- Roadmap timeline: ordered stages by priority and learning step.
- Report panel: generated Korean summary with clear caveats.
- Method panel: retrieval mode, embedding model, scoring formula, RAG scope.

## Interaction

- The user should be able to paste text or upload files without understanding internal JSON.
- Loading should clearly indicate whether the app is extracting text, analyzing gaps, or retrieving resources.
- Errors should say what failed: URL extraction, file parsing, insufficient text, analysis failure, or recommendation failure.
- The app should keep the user’s pasted text if an error occurs.

## Motion

Use short 150-220ms transitions for hover, focus, panel reveal, and score bars. Avoid decorative page-load choreography. Respect `prefers-reduced-motion`.

## Content

Labels are Korean-first. Technical terms like RAG, gap score, embedding, and Top-K may appear only in method disclosure areas. Primary headings should use user-facing language such as `채용공고 분석`, `지원자 자료`, `보완 필요 역량`, and `학습 로드맵`.
