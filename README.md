# 채용공고 기반 직무 분류와 역량 격차 분석 및 RAG 학습 로드맵 추천 시스템

Generated: 2026-05-21
Status: Product-direction update for final implementation
Course Context: 자연어처리 기말 프로젝트

## 1. 프로젝트 정의

이 프로젝트는 사용자가 지원하려는 채용공고와 본인의 자소서, 이력서, 포트폴리오 자료를 입력하면, 시스템이 자연어처리 기법으로 직무군과 역량 격차를 분석하고 부족 역량을 보완할 학습 로드맵과 추천 자료를 제공하는 시스템이다.

핵심은 데모용 구조화 입력을 받는 추천기가 아니라, 실제 사용자가 가진 원본 자료를 입력받아 다음 질문에 답하는 것이다.

- 이 채용공고는 어떤 직무군에 가까운가?
- 채용공고에서 요구하는 핵심 역량은 무엇인가?
- 지원자 자료에 드러난 보유 역량은 무엇인가?
- 요구 역량 대비 부족한 역량은 무엇이고, 부족 정도는 어느 정도인가?
- 어떤 순서로 공부해야 하며, 어떤 학습 자료를 봐야 하는가?

## 2. 입력 방식

사용자는 채용공고와 지원자 자료를 여러 형태로 입력할 수 있다.

### 채용공고 입력

- 채용공고 URL
- 채용공고 본문 텍스트 붙여넣기
- 채용공고 PDF 또는 TXT 파일 업로드

### 지원자 자료 입력

- 자소서 텍스트 붙여넣기
- 이력서 PDF 또는 TXT 파일 업로드
- 포트폴리오 설명 텍스트
- GitHub README 또는 프로젝트 설명 텍스트

DOCX, HWP, 복수 파일 업로드는 확장 기능으로 둔다. 최종 버티컬 슬라이스에서는 텍스트와 PDF/TXT를 우선 안정적으로 처리한다.

## 3. 출력 결과

시스템은 대시보드와 리포트를 함께 제공한다.

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
  "skill_gaps": [
    {
      "skill": "Docker",
      "gap_score": 82,
      "gap_level": "높음",
      "importance": "필수",
      "evidence": "채용공고에는 Docker 배포 경험이 요구되지만 지원자 자료에는 관련 경험이 명확히 나타나지 않음"
    }
  ],
  "learning_roadmap": [
    {
      "priority": 1,
      "skill": "Docker",
      "steps": [
        "Docker 기본 개념 학습",
        "Dockerfile 작성 실습",
        "백엔드 API 컨테이너화",
        "Docker Compose로 DB와 함께 실행"
      ],
      "recommended_resources": [
        "Docker 공식 문서",
        "Docker 입문 실습 자료"
      ],
      "practice_project": "간단한 REST API를 Docker로 패키징하고 실행 방법을 README에 정리하기"
    }
  ],
  "summary_report": "지원자는 백엔드 개발 기본 역량은 갖추고 있으나, 배포 및 운영 관련 역량이 부족하므로 Docker, AWS, CI/CD 순서로 보완하는 것을 추천합니다."
}
```

## 4. 전체 시스템 흐름

```text
채용공고 URL/텍스트/파일 입력
지원자 자소서/이력서/포트폴리오 텍스트/파일 입력
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
역량 격차 분석 및 gap_score 산출
        ↓
부족 역량을 query로 변환
        ↓
learning_resources.csv 기반 RAG 검색
        ↓
추천 점수 계산 및 Top-K 자료 선정
        ↓
학습 로드맵 및 자연어 리포트 생성
        ↓
대시보드 출력
```

## 5. RAG 정의

이 프로젝트의 RAG는 웹 전체를 실시간 검색하는 구조가 아니다. 직접 큐레이션한 `learning_resources.csv` 학습자료 DB를 검색하는 추천형 RAG다.

```text
부족 역량 + 근거 문장
        ↓
학습자료 메타데이터 검색
        ↓
관련 자료 Top-K 추출
        ↓
추천 점수 재계산
        ↓
로드맵과 리포트 생성
```

학습자료 DB는 다음 정보를 포함한다.

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

## 6. 추천 점수 공식

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

- `semantic_similarity`: 부족 역량 query와 학습자료 설명 간 의미 유사도, 0~1
- `skill_match`: 부족 역량이 자료 메타데이터에 직접 매칭되면 1, 아니면 0
- `job_group_match`: 예측 직무군과 자료 직무군이 같으면 1, 아니면 0
- `reliability_norm`: `reliability / 5`

최종 설계에서는 OpenAI `text-embedding-3-small` 기반 임베딩 검색을 사용한다. API key가 없거나 실패하면 TF-IDF 검색으로 fallback할 수 있다.

## 7. 현재 구현 상태와 반드시 고쳐야 할 점

현재 저장소에는 학습자료 DB, 추천 점수 계산, 로드맵 생성, 리포트 생성, 대시보드 일부가 구현되어 있다. 하지만 현재 코드는 아직 최종 제품 정의와 완전히 일치하지 않는다.

현재 남은 핵심 작업:

- 기존 구조화 입력 전용 UI 제거
- 데모 데이터 버튼 제거
- 채용공고 URL/텍스트/파일 입력 UI 추가
- 자소서/이력서/포트폴리오 텍스트/파일 입력 UI 추가
- 원본 입력에서 요구 역량과 보유 역량을 추출하는 `/analyze` API 추가
- 부족 역량과 gap_score를 시스템이 직접 계산하도록 연결
- 기존 추천 로직을 `/analyze` 결과 뒤에 자동 연결

즉 현재 구현은 추천 파이프라인의 후반부가 먼저 만들어진 상태이며, 최종 제품이 되려면 원본 입력 분석 파이프라인을 앞단에 붙여야 한다.

## 8. 실행 방법

백엔드:

```bash
uv venv .venv
uv pip install --python .venv -r backend/requirements.txt
export OPENAI_API_KEY="..."
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

프론트엔드:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8010 npm run dev -- --hostname 127.0.0.1 --port 3010
```

현재 개발 서버 기준:

- 백엔드: `http://127.0.0.1:8010`
- 프론트엔드: `http://127.0.0.1:3010`

## 9. 평가 방법

### 직무 분류 평가

- Accuracy
- Precision
- Recall
- Macro F1-score
- Confusion Matrix

### 역량 격차 분석 평가

- 사람이 라벨링한 요구 역량과 시스템 추출 결과 비교
- 사람이 라벨링한 보유 역량과 시스템 추출 결과 비교
- 부족 역량 판단의 Precision, Recall, F1-score
- gap_score 구간의 타당성 검토

### 추천 평가

- 부족 역량과 추천 자료의 관련성
- 추천 자료의 난이도 적절성
- 학습 순서의 타당성
- 실습 프로젝트가 부족 역량을 보완하는지 여부

## 10. 최종 한 줄 설명

본 프로젝트는 채용공고와 지원자 자료를 NLP로 분석하여 직무군, 적합도, 부족 역량과 부족 정도를 계산하고, RAG 기반 학습자료 검색을 통해 개인 맞춤형 학습 로드맵과 분석 리포트를 제공하는 시스템이다.
