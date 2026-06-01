# Evaluation Results

Generated: 2026-05-28

## Backend Tests

Command:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover backend/tests
```

Exit code: `0`

```text
Ran 34 tests in 2.185s

OK
```

Notes:

- `backend/tests/test_c_part_pipeline.py` verifies packaged C pipeline behavior with fake embeddings.
- `backend/tests/test_partial_recommendations.py` verifies `skill_gaps` are recommended before `partial_skills`.
- `backend/tests/test_analyze_api.py` verifies `/analyze` passes A/B `classification.job_label` into C as `b_predicted_job`.

## Learning Resource DB Audit

Command:

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py
```

Exit code: `0`

```text
resource_count=86
job_group_counts={'AI/ML 엔지니어': 20, '데이터 분석가': 20, '백엔드 개발자': 26, '프론트엔드 개발자': 20}
taxonomy_skill_count=65
missing_taxonomy_skill_count=0
duplicate_url_count=0
invalid_reliability_count=0
audit_status=PASS
```

## Recommendation Metrics

Command:

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/evaluate_recommendations.py
```

Exit code: `0`

```text
case_count=8
hit_at_3=0.875
precision_at_3=0.792
difficulty_match_rate=1.000
```

## Frontend Build

Command:

```bash
npm --prefix frontend run build
```

Exit code: `0`

```text
> jd-skill-gap-rag-dashboard@0.1.0 build
> next build

✓ Compiled successfully in 1119ms
Running TypeScript ...
Finished TypeScript in 965ms ...
✓ Generating static pages using 4 workers (3/3) in 166ms
```

## Frontend Typecheck Gate

Command:

```bash
npm --prefix frontend run typecheck --if-present
```

Exit code: `0`

Note: `frontend/package.json` currently has no `typecheck` script, so `next build` is the active TypeScript gate.

## Added Resource URL Check

Command:

```bash
curl -L -o /dev/null -s -w '%{http_code}' --max-time 12 <url>
```

Result:

```text
200 https://kubernetes.io/ko/docs/home/
200 https://www.inflearn.com/ko/search?s=Kubernetes
200 https://kafka.apache.org/documentation/
200 https://www.inflearn.com/ko/search?s=Kafka
200 https://junit.org/junit5/docs/current/user-guide/
200 https://www.inflearn.com/ko/search?s=JUnit
```

## Current Integration Status

Implemented flow:

```text
사용자 입력
  -> A/B 앙상블 직무 분류
  -> C pipeline 역량 격차 분석
  -> D curated RAG 추천
  -> 주차별 로드맵
  -> 리포트
  -> Next.js 대시보드
```

Important output categories:

- `owned_skills`: 충분히 충족한 역량, 추천 제외
- `partial_skills`: 일부 경험은 있으나 기준 미달, 낮은 우선순위 추천
- `skill_gaps`: 근거가 없거나 크게 부족한 역량, 높은 우선순위 추천

Remaining integration caveat:

- Real C embedding model `jhgan/ko-sroberta-multitask` has been downloaded into the local HuggingFace cache on this machine. Other machines must download the same model or run with network access.

## C Model Download And No-Mock Smoke

Downloaded target:

```text
jhgan/ko-sroberta-multitask
snapshot=1050bd4e2ca90c0b9b62f0c1fbd83edc85ba8483
weight_file=model.safetensors
cache_size=739M
incomplete_files=0
```

Offline model load check:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 .venv/bin/python - <<'PY'
from transformers import AutoTokenizer, AutoModel
model_id = "jhgan/ko-sroberta-multitask"
tok = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
model = AutoModel.from_pretrained(model_id, local_files_only=True)
print(tok.__class__.__name__)
print(model.__class__.__name__)
print(model.config.hidden_size)
PY
```

Result:

```text
tokenizer BertTokenizer
model RobertaModel
hidden_size 768
local_load_ok
```

No-mock `/analyze` smoke:

```text
status_code 200
predicted_job 백엔드 개발자
job_label backend
classifier_source ab_ensemble
fit_score 75.0
retrieval_mode tfidf_last_resort
embedding_model none
required_count 12
owned ['Java', 'Spring Boot', 'REST API', 'OpenAPI', 'MySQL', 'PostgreSQL', 'AWS', 'Spring Security']
partial []
missing ['Docker', 'CI/CD', 'Node.js', 'Kafka']
recommended_count 4
weekly_roadmap_count 4
```

This smoke used no mocked classifier and no mocked C embedding. `TF-IDF last resort` was used for D retrieval because OpenAI and BGE were intentionally disabled during the offline smoke.
