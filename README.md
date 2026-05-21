# JD 기반 지원자 역량 분석 D 파트

이 저장소는 자연어처리 기말 프로젝트 중 D 파트를 로컬에서 시연하기 위한 vertical slice입니다.

```text
C 파트 격차 분석 JSON
→ curated learning_resources.csv 검색
→ 추천 점수 계산
→ 학습 로드맵 생성
→ 자연어 리포트 생성
→ 로컬 대시보드 출력
```

## 현재 구현 범위

- 학습 자료 DB 80개, 직무군별 20개씩 구성
- 잡코리아 채용공고 샘플에서 반복 확인한 요구역량을 기준으로 DB 재구성
- 한국어 자료 기준으로 공식문서, 공식학습, 실습플랫폼, 유튜브, 블로그, 강의 자료 혼합
- 유튜브 자료는 직무군별 5개씩 포함하여 총 20개로 보강
- 각 자료에 `type`, `level`, `language`, `reliability`, `reason` 포함
- C 파트가 넘겨주는 `skill_gaps`를 받아 부족 역량별 Top-K 추천 생성
- 추천 점수 공식 공개
- GPU, 유료 LLM API 없이 실행되는 로컬 FastAPI + Next.js 대시보드

이 프로젝트의 RAG는 웹 전체 검색이 아니라, 직접 큐레이션한 `learning_resources.csv`를 검색하는 추천 RAG입니다.

## C 파트 입력 계약

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 72,
  "matched_skills": ["Java", "Spring Boot", "MySQL", "REST API"],
  "skill_gaps": [
    {
      "skill": "Docker",
      "gap_score": 82,
      "gap_level": "높음",
      "importance": "필수",
      "evidence": "JD에는 Docker 기반 배포 경험이 요구되지만 지원자 텍스트에는 컨테이너 기반 배포 경험이 나타나지 않음"
    }
  ]
}
```

D 파트는 부족 역량을 새로 판단하지 않습니다. 부족 역량과 격차 점수는 C 파트가 계산하고, D 파트는 그 결과를 학습 자료 추천과 로드맵으로 바꿉니다.

## 추천 점수 공식

```text
recommend_score =
100 * (
  0.6 * semantic_similarity
+ 0.2 * skill_match
+ 0.1 * job_group_match
+ 0.1 * reliability_norm
)
```

정규화 기준:

- `semantic_similarity`: 0~1, 현재는 로컬 TF-IDF cosine similarity
- `skill_match`: 부족 역량이 자료 메타데이터에 직접 매칭되면 1, 아니면 0
- `job_group_match`: 예측 직무군과 자료 직무군이 같으면 1, 아니면 0
- `reliability_norm`: `reliability / 5`

Sentence-BERT나 Chroma/FAISS를 붙일 수 있지만, 80개 DB의 발표용 vertical slice에서는 CPU 기반 TF-IDF 검색만으로 재현성과 속도가 충분합니다.

## 실행 방법

### 1. 백엔드

```bash
uv venv .venv
uv pip install --python .venv -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

확인:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/sample
```

### 2. 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://127.0.0.1:3000`을 열고 `분석 실행`을 누르면 샘플 C 출력 기반 추천 결과가 표시됩니다.

프로덕션 빌드 확인:

```bash
cd frontend
npm run build
npm run start -- --hostname 127.0.0.1 --port 3000
```

## URL 검증

학습 자료 URL이 실제로 열리는지 검증합니다.

```bash
PYTHONPATH=backend .venv/bin/python backend/tools/verify_resource_urls.py
```

검증 스크립트는 HTTP 상태 코드와 최종 redirect URL, HTML title을 출력하고 실패 URL이 있으면 non-zero exit code로 종료합니다.

## 발표용 설명

> 저는 C 파트가 계산한 부족 역량과 격차 점수를 입력으로 받아, 직접 구축한 80개 학습 자료 DB에서 관련 자료를 검색합니다. 검색된 자료는 의미 유사도, 기술 매칭, 직무군 매칭, 신뢰도 점수를 조합해 정렬하고, 그 결과를 바탕으로 학습 로드맵과 자연어 리포트를 생성합니다. 마지막으로 이 과정을 로컬 대시보드에서 확인할 수 있게 통합했습니다.

## 주요 파일

- `backend/app/data/learning_resources.csv`: 학습 자료 DB 80개
- `docs/jobkorea_skill_basis.md`: 잡코리아 기반 역량 선정 근거
- `exports/learning_resources_catalog.csv`: 확인용 한국어 CSV
- `backend/app/data/sample_c_output.json`: C 파트 샘플 출력
- `backend/app/services/retriever.py`: TF-IDF 검색기
- `backend/app/services/scorer.py`: 추천 점수 공식
- `backend/app/services/roadmap_generator.py`: 학습 로드맵 생성
- `backend/app/services/report_generator.py`: 자연어 리포트 생성
- `backend/app/main.py`: FastAPI 엔드포인트
- `frontend/app/page.tsx`: 로컬 대시보드 화면
