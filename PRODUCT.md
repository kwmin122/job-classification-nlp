# Product

## Register

product

## Users

The primary user is a job seeker preparing for a specific job posting. They provide the target job posting and their own application materials, then choose how much time they have and what difficulty level they want. Reviewers and classmates use the app to understand the full NLP pipeline from raw input to skill-gap analysis and learning-roadmap recommendation.

## Product Purpose

The product analyzes a target job posting and candidate materials, identifies the job group, extracts required and owned skills, calculates missing skills with gap scores, and recommends learning resources and a weekly roadmap based on the user's selected duration and difficulty.

## User Inputs

- Job posting URL, pasted job posting text, or uploaded PDF/TXT job posting.
- Candidate cover letter, resume, portfolio text, GitHub README text, or uploaded PDF/TXT candidate document.
- Roadmap duration: 2, 4, 8, or 12 weeks.
- Current level: 입문, 기초, 실무, 심화.
- Learning intensity: 가볍게, 보통, 집중.

DOCX, HWP, multi-file uploads, and account storage are expansion targets after the first stable vertical slice.

## Product Outputs

- Predicted job group.
- Fit score.
- Required skills with job-posting evidence.
- Owned skills with candidate-material evidence.
- Missing skills with `gap_score`, `gap_level`, importance, and evidence.
- Recommended learning resources.
- Weekly roadmap adjusted by duration, level, and intensity.
- Practice project suggestions.
- Natural-language analysis report.

## Brand Personality

Calm, credible, practical. The interface should feel like a focused career analysis tool, not a generic AI chatbot, team demo, or marketing landing page.

## Anti-references

Do not expose internal team-role language in the user-facing flow. Do not make the primary interaction a raw structured-data textarea. Avoid gradient text, glassmorphism, nested cards, decorative charts, and vague AI claims.

## Design Principles

1. Start from the user’s real task: compare my application materials against this job posting.
2. Ask for learning constraints before generating a roadmap: duration, current level, intensity.
3. Show evidence: every gap should connect to a job-posting requirement and candidate-material evidence or absence.
4. Keep the RAG claim honest: recommendations come from a curated learning-resource DB, not open-web search.
5. Separate analysis from recommendation: first calculate gaps, then recommend resources and schedule them.
6. Keep demo reliability: text and PDF/TXT should work before broader document formats are added.

## Accessibility & Inclusion

Target WCAG AA contrast, keyboard-reachable controls, visible focus states, and Korean-first labels with English technical terms where common. Avoid unnecessary motion and respect reduced-motion preferences.
