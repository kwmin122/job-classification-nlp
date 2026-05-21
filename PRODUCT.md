# Product

## Register

product

## Users

The primary users are job seekers preparing for a specific job posting. They provide a target job posting and their own application materials, such as a cover letter, resume, portfolio text, GitHub README, or uploaded PDF/TXT files. Reviewers and classmates use the app to understand the full NLP pipeline from raw documents to skill-gap analysis and learning-roadmap recommendation.

## Product Purpose

This product analyzes a job posting and candidate materials, identifies the target job group, extracts required and owned skills, calculates missing skills with gap scores, and recommends learning resources from a curated resource database. It must produce the gap analysis from user-provided raw inputs, then use the RAG recommendation pipeline.

## Input Contract

The product accepts:

- Job posting URL, pasted job posting text, or uploaded PDF/TXT job posting.
- Candidate cover letter, resume, portfolio text, GitHub README text, or uploaded PDF/TXT candidate document.

DOCX, HWP, and multi-file upload are expansion targets after the first stable vertical slice.

## Output Contract

The product returns:

- Predicted job group.
- Fit score.
- Required skills with job-posting evidence.
- Owned skills with candidate-evidence sentences.
- Missing skills with `gap_score`, `gap_level`, importance, and evidence.
- Recommended learning resources.
- Prioritized learning roadmap.
- Natural-language analysis report.

## Brand Personality

Calm, credible, practical. The interface should feel like a focused career analysis tool. It should not feel like an internal team-role demo, a JSON contract tester, a generic AI chatbot, or a marketing landing page.

## Anti-references

Do not expose internal team-role language or developer-only payload contracts in the user-facing flow. Do not make the primary interaction a structured debug textarea. Avoid gradient text, glassmorphism, nested cards, decorative charts, and vague AI claims.

## Design Principles

1. Start from the user’s real task: compare my application materials against this job posting.
2. Show evidence: every gap should connect to a job-posting requirement and candidate-material evidence or absence.
3. Keep the RAG claim honest: recommendations come from a curated learning-resource DB, not open-web search.
4. Separate analysis from recommendation: first calculate gaps, then recommend resources.
5. Keep demo reliability: text and PDF/TXT should work before broader document formats are added.

## Accessibility & Inclusion

Target WCAG AA contrast, keyboard-reachable controls, visible focus states, and Korean-first labels with English technical terms where common. Avoid unnecessary motion and respect reduced-motion preferences.
