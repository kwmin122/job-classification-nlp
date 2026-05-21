# Product Direction Merge Report

Updated: 2026-05-21

## Result

The revised product direction is user-centered. The product must analyze real user inputs: a job posting link/text/file plus candidate cover letter, resume, portfolio, or GitHub README text/file.

## Revised Merge Decision

The accepted direction is:

```text
raw job posting + raw candidate materials
→ text extraction
→ job classification
→ required/owned skill extraction
→ missing skill + gap score calculation
→ curated learning-resource RAG
→ preference-aware weekly roadmap + report
```

## Consequence

Any remaining document or implementation plan that treats prepared gap data as the main user input is outdated. Prepared analysis data can exist for tests, but the product path must start from user-provided job and candidate materials.
