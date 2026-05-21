# Dashboard Redesign Merged Plan

Updated: 2026-05-21

## Objective

The dashboard must become a real user-facing product flow. The user provides a job posting and their own candidate materials, then receives skill-gap analysis, recommended learning resources, a roadmap, and a report.

## Key Decision

The previous product-facing redesign removed internal role labels, but it still assumed a developer payload input. That is not enough. The next design target replaces that primary input with real document inputs.

## Information Architecture

1. Job posting input: URL, text, PDF/TXT.
2. Candidate material input: cover letter/resume/portfolio text, PDF/TXT.
3. Analysis progress: extract text, classify job, compare skills, retrieve resources.
4. Result summary: predicted job, fit score, missing skill count, top priority.
5. Evidence: required skills, owned skills, missing skills, gap scores.
6. Recommendations: learning resources grouped by missing skill.
7. Roadmap and report.

## Visual Direction

Use restrained product UI. The first screen should feel like a career analysis tool, not a JSON debugger or a team demo. Keep tables, score bars, resource rows, and timeline output because they support evidence-based explanation.

## Implementation Implication

Frontend changes alone are insufficient. The backend needs a new `/analyze` flow that accepts raw job-posting and candidate inputs, calculates gaps, then calls the existing RAG recommendation pipeline.
