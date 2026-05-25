# JD 기반 지원자 역량 분석 및 맞춤형 학습 로드맵 추천 시스템

Generated: 2026-05-21
Status: User-centered final product plan
Course Context: 자연어처리 기말 프로젝트

## 1. 제품 정의

사용자는 지원하려는 채용공고와 자신의 자소서, 이력서, 포트폴리오 자료를 입력한다. 시스템은 채용공고의 요구 역량과 지원자 자료의 보유 역량을 비교해 직무 적합도, 부족 역량, 부족 정도, 근거 문장, 추천 학습 자료, 주차별 학습 로드맵, 자연어 분석 리포트를 제공한다.

사용자가 알고 싶은 질문은 다음이다.

- 이 채용공고는 어떤 직무군에 가까운가?
- 내 자료는 이 채용공고에 얼마나 맞는가?
- 채용공고에서 요구하지만 내 자료에 부족하게 드러난 역량은 무엇인가?
- 부족 정도는 어느 정도인가?
- 내 현재 수준과 목표 기간에 맞춰 무엇부터 공부해야 하는가?
- 어떤 자료와 실습 과제로 포트폴리오 증거를 만들 수 있는가?

## 2. 사용자 입력

### 채용공고

- 채용공고 URL
- 채용공고 본문 텍스트
- 채용공고 PDF/TXT 파일

### 지원자 자료

- 자소서 텍스트
- 이력서 PDF/TXT 파일
- 포트폴리오 설명
- GitHub README 또는 프로젝트 설명 텍스트

### 학습 목표 설정

- 로드맵 기간: 2주, 4주, 8주, 12주
- 현재 수준: 입문, 기초, 실무, 심화
- 학습 강도: 가볍게, 보통, 집중

DOCX, HWP, 복수 파일 업로드는 확장 기능으로 둔다. 현재 구현된 안정 세로 조각은 채용공고 본문 텍스트와 지원자 자료 텍스트 입력을 우선 지원한다. URL, PDF/TXT 파일 추출은 다음 단계의 입력 어댑터로 분리한다.

## 3. 출력 결과

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 78,
  "required_skills": [
    {
      "skill": "Docker",
      "importance": "필수",
      "evidence": "채용공고에서 Docker 기반 배포 경험을 요구함"
    }
  ],
  "owned_skills": [
    {
      "skill": "Spring Boot",
      "evidence": "지원자 자료에서 Spring Boot 기반 API 개발 경험이 확인됨"
    }
  ],
  "missing_skills": [
    {
      "skill": "Docker",
      "gap_score": 82,
      "gap_level": "높음",
      "importance": "필수",
      "evidence": "채용공고에는 Docker 배포 경험이 요구되지만 지원자 자료에는 관련 경험이 명확히 나타나지 않음"
    }
  ],
  "roadmap_preferences": {
    "duration_weeks": 4,
    "difficulty": "입문",
    "intensity": "보통"
  },
  "weekly_roadmap": [
    {
      "week": 1,
      "goal": "Docker 기본 개념과 컨테이너 실행 이해",
      "skills": ["Docker"],
      "recommended_resources": ["Docker 공식 Get Started"],
      "practice": "간단한 REST API를 Docker 컨테이너로 실행"
    }
  ],
  "summary_report": "지원자는 백엔드 개발 기본 역량은 갖추고 있으나 Docker, AWS, CI/CD 기반 배포 경험이 부족합니다. 4주 입문 로드맵 기준으로 Docker 기초부터 시작해 AWS 배포와 CI/CD 자동화 순서로 보완하는 것을 추천합니다."
}
```

## 4. 전체 시스템 흐름

```text
채용공고 URL/텍스트/파일 입력
지원자 자소서/이력서/포트폴리오 텍스트/파일 입력
로드맵 기간, 현재 수준, 학습 강도 선택
        ↓
텍스트 추출 및 전처리
        ↓
채용공고 직무 분류
        ↓
JD 요구 역량 추출
지원자 보유 역량 추출
        ↓
의미 기반 유사도 계산
        ↓
부족 역량 및 gap_score 산출
        ↓
부족 역량과 사용자 선호를 query로 변환
        ↓
learning_resources.csv 기반 추천 검색
        ↓
난이도, 직무군, 신뢰도, 의미 유사도 기반 추천 점수 계산
        ↓
주차별 학습 로드맵 및 리포트 생성
        ↓
대시보드 출력
```

## 5. 추천형 RAG 정의

이 프로젝트의 RAG는 웹 전체를 실시간 검색하는 구조가 아니다. 직접 큐레이션한 `learning_resources.csv` 학습자료 DB를 검색하는 추천형 RAG다.

검색 대상은 학습자료 메타데이터다.

- `title`: 자료 제목
- `description`: 자료 설명
- `url`: 자료 링크
- `skill`: 관련 역량
- `sub_skill`: 세부 주제
- `job_group`: 추천 직무군
- `level`: beginner, intermediate, advanced
- `type`: 공식문서, 유튜브, 블로그, 책, 실습플랫폼, 강의
- `reliability`: 1~5 신뢰도
- `reason`: 이 자료를 넣은 이유

## 6. 추천 점수

기본 추천 점수는 다음 요소를 사용한다.

```text
recommend_score =
100 * (
  0.55 * semantic_similarity
+ 0.20 * skill_match
+ 0.10 * job_group_match
+ 0.10 * difficulty_match
+ 0.05 * reliability_norm
)
```

정규화 기준:

- `semantic_similarity`: 부족 역량 query와 학습자료 설명 간 의미 유사도, 0~1
- `skill_match`: 부족 역량이 자료 메타데이터와 직접 매칭되면 1, 아니면 0
- `job_group_match`: 예측 직무군과 자료 직무군이 같으면 1, 아니면 0
- `difficulty_match`: 사용자가 선택한 현재 수준과 자료 난이도가 맞으면 1, 가까우면 0.5, 멀면 0
- `reliability_norm`: `reliability / 5`

최종 검색은 OpenAI `text-embedding-3-small` 기반 임베딩 검색을 목표로 한다. API key가 없거나 실패하면 무료 로컬 임베딩 모델인 `BAAI/bge-m3`로 fallback한다. 로컬 모델 로딩까지 실패한 경우에만 TF-IDF를 마지막 안전장치로 사용한다.

## 7. 현재 구현 상태

구현되어 있는 것:

- 학습자료 DB 80개
- `learning_resources.csv` 기반 추천형 RAG 검색
- OpenAI `text-embedding-3-small` 임베딩 검색, API key가 없을 때 `BAAI/bge-m3` 로컬 임베딩 fallback
- 1행 1자료 기준 chunking
- 추천 점수 계산: 의미 유사도, 역량 일치, 직무군 일치, 난이도 일치, 신뢰도 반영
- 채용공고 텍스트와 지원자 텍스트를 받는 `/analyze` 통합 API
- `skill_taxonomy.json` 기반 직무군/역량 후보 로딩
- `analyzer_rules.json` 기반 부정 표현, 필수/우대, gap score 기준 로딩
- 부족 역량, gap score, fit score 계산
- 사용자가 선택한 기간/난이도/강도를 반영한 주차별 로드맵 생성
- 자연어 리포트 생성
- 실제 사용자 관점의 로컬 Next.js 대시보드

아직 필요한 것:

- 채용공고 URL 입력 어댑터
- 채용공고 PDF/TXT 파일 업로드와 텍스트 추출
- 지원자 자료 PDF/TXT 파일 업로드와 텍스트 추출
- URL 본문 추출
- B팀 직무 분류 모델과의 실제 연결
- C팀 Ko-Sentence-BERT 기반 의미 유사도 격차 분석과의 실제 연결
- LLM API 기반 리포트 생성. 현재는 계산 결과를 템플릿으로 설명한다.

하드코딩 금지 기준:

- 제품 결과를 만들기 위해 코드 안에 특정 직무, 특정 역량, 특정 점수를 박지 않는다.
- 역량 후보와 직무군 키워드는 `backend/app/data/skill_taxonomy.json`에서 관리한다.
- 부정 표현, 필수/우대 판정, gap score 기준은 `backend/app/data/analyzer_rules.json`에서 관리한다.
- 로컬 서버 주소는 코드에 고정하지 않고 `BACKEND_ORIGIN`, `NEXT_PUBLIC_API_URL`, `ALLOWED_ORIGINS`, `ALLOW_LOCALHOST_CORS`로 주입한다.
- 테스트 fixture와 문서 예시는 검증/설명용으로만 사용하고, 실제 `/analyze` 결과 생성 경로에는 사용하지 않는다.

## 8. 실행 방법

백엔드:

```bash
uv venv .venv
uv pip install --python .venv -r backend/requirements.txt
export OPENAI_API_KEY="..."
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port <BACKEND_PORT>
```

프론트엔드:

```bash
cd frontend
npm install
BACKEND_ORIGIN=http://127.0.0.1:<BACKEND_PORT> npm run dev -- --hostname 127.0.0.1 --port <FRONTEND_PORT>
```

프론트는 기본적으로 `/api`를 호출하고, Next.js rewrite가 `BACKEND_ORIGIN`으로 프록시한다. 배포나 팀원 환경에서 포트가 바뀌어도 코드 수정 없이 환경값만 바꾸면 된다.

## 9. 평가 계획

### 직무 분류

- Accuracy
- Precision
- Recall
- Macro F1-score
- Confusion Matrix

### 역량 격차 분석

- 요구 역량 추출 Precision, Recall, F1-score
- 보유 역량 추출 Precision, Recall, F1-score
- 부족 역량 판단 Precision, Recall, F1-score
- gap_score 구간 타당성 검토

### 추천과 로드맵

- Hit@K
- Precision@K
- 추천 자료 난이도 적합률
- 주차별 로드맵 완성도 검토
- 추천 자료 URL 유효성

실제 성능 수치는 실험 후 기록한다. 발표에서는 임의 수치를 넣지 않는다.

## 10. 최종 한 줄 설명

본 프로젝트는 사용자가 입력한 채용공고와 지원자 자료를 NLP로 분석하여 직무 적합도와 부족 역량을 계산하고, 사용자가 선택한 학습 기간과 난이도에 맞춰 RAG 기반 학습자료와 주차별 로드맵을 추천하는 시스템이다.
