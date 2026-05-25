# Evaluation Results

Generated: 2026-05-25

## Backend Tests

Command: `/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp/.venv/bin/python -m unittest discover -s backend/tests`

Exit code: `0`

```text
...................
----------------------------------------------------------------------
Ran 19 tests in 0.016s

OK
```

## Learning Resource DB Audit

Command: `/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp/.venv/bin/python backend/tools/audit_learning_resources.py`

Exit code: `0`

```text
resource_count=80
job_group_counts={'AI/ML 엔지니어': 20, '데이터 분석가': 20, '백엔드 개발자': 20, '프론트엔드 개발자': 20}
duplicate_url_count=0
invalid_reliability_count=0
audit_status=PASS
```

## Recommendation Metrics

Command: `/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp/.venv/bin/python backend/tools/evaluate_recommendations.py`

Exit code: `0`

```text
case_count=8
hit_at_3=0.875
precision_at_3=0.792
difficulty_match_rate=1.000
```

## Frontend Build

Command: `npm run build`

Exit code: `0`

```text
> jd-skill-gap-rag-dashboard@0.1.0 build
> next build

▲ Next.js 16.2.6 (Turbopack)

  Creating an optimized production build ...
✓ Compiled successfully in 686ms
  Running TypeScript ...
  Finished TypeScript in 815ms ...
  Collecting page data using 4 workers ...
  Generating static pages using 4 workers (0/3) ...
✓ Generating static pages using 4 workers (3/3) in 148ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
└ ○ /_not-found


○  (Static)  prerendered as static content
```
