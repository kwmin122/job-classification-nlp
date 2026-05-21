# Merge Report

Updated: 2026-05-21

## Result

The previous merge correctly removed internal D/C language from the visible dashboard, but the user clarified that this is not sufficient. The product must analyze real user inputs: job posting link/text/file plus candidate cover letter/resume/portfolio text/file.

## Revised Merge Decision

The accepted direction is:

```text
raw job posting + raw candidate materials
→ text extraction
→ job classification
→ required/owned skill extraction
→ missing skill + gap score calculation
→ curated learning-resource RAG
→ roadmap + report
```

## Consequence

Any remaining document or implementation plan that treats precomputed gap data as the primary user input is outdated.
