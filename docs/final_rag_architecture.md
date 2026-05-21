# 최종 분석 및 RAG 학습 로드맵 설계

Generated: 2026-05-21
Status: User-centered architecture target

## 1. 핵심 방향

최종 시스템은 사용자가 입력한 채용공고와 지원자 자료를 직접 분석한다. 사용자는 로드맵 기간과 난이도를 선택하고, 시스템은 그 조건에 맞춰 학습자료와 주차별 계획을 생성한다.

```text
채용공고 URL/텍스트/파일
지원자 자소서/이력서/포트폴리오 텍스트/파일
로드맵 기간, 현재 수준, 학습 강도
        ↓
텍스트 추출
        ↓
직무 분류
        ↓
요구 역량 추출
보유 역량 추출
        ↓
부족 역량과 gap_score 계산
        ↓
학습자료 DB 검색
        ↓
난이도와 기간을 반영한 추천 점수 계산
        ↓
주차별 로드맵과 리포트 생성
```

## 2. 입력 계층

### 채용공고 입력

- URL 입력
- 본문 텍스트 붙여넣기
- PDF/TXT 파일 업로드

URL 입력은 가능한 경우 HTML 본문을 추출한다. 채용 사이트 구조가 다르거나 차단되면 사용자에게 텍스트 붙여넣기를 요청한다.

### 지원자 자료 입력

- 자소서 텍스트
- 이력서 PDF/TXT 파일
- 포트폴리오 설명
- GitHub README 또는 프로젝트 설명 텍스트

### 학습 목표 입력

- `duration_weeks`: 2, 4, 8, 12
- `difficulty`: 입문, 기초, 실무, 심화
- `intensity`: 가볍게, 보통, 집중

## 3. 텍스트 추출 및 전처리

- PDF/TXT에서 텍스트 추출
- URL HTML에서 본문 후보 추출
- 불필요한 공백과 중복 줄 제거
- 문장 단위 분리
- 기술명 표기 정규화
- 너무 짧거나 의미 없는 문장 제거

DOCX/HWP는 확장 기능이다. 현재 구현된 안정 세로 조각은 텍스트 입력을 우선 지원한다. URL과 PDF/TXT는 같은 `/analyze` 계약에 붙일 입력 어댑터로 남겨 둔다.

## 4. 직무 분류

지원 직무군은 4개로 제한한다.

- 데이터 분석가
- AI/ML 엔지니어
- 백엔드 개발자
- 프론트엔드 개발자

모델 비교는 수업 내용 연결과 실제 실험을 위해 유지한다.

| 모델 | 역할 | 평가 |
|---|---|---|
| TF-IDF + SVM | baseline | Accuracy, Macro F1 |
| LSTM | 순서 정보 반영 비교 | Accuracy, Macro F1 |
| Text-CNN | 기술 표현 패턴 비교 | Accuracy, Macro F1 |
| KoBERT/BERT | 최종 후보 | Accuracy, Macro F1 |

성능 수치는 실제 실험 후 기록한다.

## 5. 역량 추출과 격차 분석

채용공고에서는 요구 역량을 추출한다.

- 기술명
- 요구 경험
- 필수/우대 여부
- 근거 문장

지원자 자료에서는 보유 역량을 추출한다.

- 기술명
- 프로젝트 경험
- 도구 사용 경험
- 근거 문장

각 요구 역량은 지원자 자료와 의미 유사도로 비교한다. gap score는 0~100으로 표현한다.

| 구간 | 의미 |
|---:|---|
| 0~39 | 낮음, 표현 보완 또는 심화 수준 |
| 40~69 | 중간, 실습 경험 보강 필요 |
| 70~100 | 높음, 핵심 경험 부족 |

gap score는 다음 요소를 조합한다.

- 채용공고에서의 중요도
- 지원자 자료에서의 직접 언급 여부
- 의미 유사도
- 근거 문장 존재 여부
- 직무별 필수 역량 여부

현재 세로 조각에서는 C팀의 최종 Ko-Sentence-BERT 격차 분석기가 아직 연결되지 않았으므로, `skill_taxonomy.json`과 `analyzer_rules.json`을 읽어 기술명 근거와 부정 표현을 기준으로 1차 gap score를 계산한다. 고정된 `gap_score=80`을 반환하지 않고, 필수/우대 여부와 지원자 자료의 명시적 부정 표현 여부를 반영한다.

## 6. RAG 검색 대상

RAG 검색 대상은 `backend/app/data/learning_resources.csv`다. 웹 전체를 실시간 검색하지 않는다.

학습자료 1행을 chunk 1개로 본다.

```text
chunk text =
job_group + skill + sub_skill + title + description + reason + level + type
```

이 프로젝트는 긴 문서 질의응답 RAG가 아니라 학습자료 메타데이터 추천 RAG다.

## 7. 임베딩 모델

최종 추천 검색은 OpenAI `text-embedding-3-small`을 기준으로 설계한다.

선택 이유:

- 한국어 설명과 영어 기술명이 섞인 자료에 대응 가능
- API 호출만으로 embedding 생성 가능
- 80개 자료 규모에서는 별도 벡터 DB 서버 없이도 충분함
- 발표 재현성이 좋음
- 비용과 구현 복잡도가 낮음

API key가 없거나 실패하면 TF-IDF 검색으로 fallback한다. fallback은 데모 안정성을 위한 장치이지 최종 성능 주장 모델이 아니다.

## 8. 추천 점수

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

`difficulty_match`는 사용자 현재 수준과 자료 난이도 간 적합도를 반영한다.

| 사용자 수준 | 우선 추천 자료 |
|---|---|
| 입문 | beginner, 공식 튜토리얼, 쉬운 강의 |
| 기초 | beginner~intermediate, 실습 자료 |
| 실무 | intermediate, 프로젝트형 자료 |
| 심화 | intermediate~advanced, 운영/최적화 자료 |

## 9. 주차별 로드맵 생성

로드맵은 사용자가 선택한 기간에 맞춰 생성한다.

| 기간 | 구성 |
|---|---|
| 2주 | 핵심 부족 역량 1~2개 집중 |
| 4주 | 핵심 부족 역량 2~3개 순차 보완 |
| 8주 | 기초, 실습, 프로젝트 적용, 포트폴리오 정리 |
| 12주 | 심화 학습과 운영/최적화까지 포함 |

학습 강도는 주차별 과제 수와 자료 수를 조절한다.

| 강도 | 주차별 권장 활동 |
|---|---|
| 가볍게 | 핵심 자료 1개 + 짧은 실습 |
| 보통 | 자료 2개 + 실습 1개 |
| 집중 | 자료 2~3개 + 프로젝트 적용 |

## 10. 리포트 생성

리포트 생성은 새로운 판단을 하는 단계가 아니다. 이미 계산된 분석 결과와 추천 자료를 사람이 읽기 좋게 설명한다.

리포트는 다음을 포함한다.

- 예측 직무
- 적합도
- 요구 역량
- 보유 역량
- 부족 역량과 gap score
- 부족하다고 판단한 근거
- 사용자가 선택한 기간과 난이도
- 주차별 학습 계획
- 추천 자료와 실습 과제
- 한계와 주의점

## 11. API 구조 목표

### `POST /analyze`

원본 채용공고, 지원자 자료, 로드맵 선호를 입력받아 전체 분석과 추천을 수행한다.

```json
{
  "job_posting": {
    "source_type": "url",
    "url": "https://example.com/job/123",
    "text": ""
  },
  "candidate_materials": [
    {
      "source_type": "text",
      "label": "자소서",
      "text": "지원자 자기소개서 본문"
    }
  ],
  "roadmap_preferences": {
    "duration_weeks": 4,
    "difficulty": "입문",
    "intensity": "보통"
  }
}
```

### Response

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 78,
  "required_skills": [],
  "owned_skills": [],
  "missing_skills": [],
  "recommended_resources": [],
  "weekly_roadmap": [],
  "report": ""
}
```

## 12. 현재 구현 격차

구현되어 있는 것:

- 학습자료 DB 80개
- `learning_resources.csv` 기반 추천형 RAG 검색
- OpenAI `text-embedding-3-small` 임베딩 검색과 TF-IDF fallback
- 추천 점수 계산
- 사용자 기간/난이도/강도 기반 주차별 로드맵 생성
- 계산 결과 기반 자연어 리포트 생성
- `/analyze` 통합 API
- `skill_taxonomy.json` 기반 직무군/역량 후보 로딩
- `analyzer_rules.json` 기반 부정 표현, 중요도, gap score 기준 로딩
- 실제 사용자 관점의 로컬 대시보드

아직 필요한 것:

- 채용공고 URL 입력 어댑터
- PDF/TXT 파일 업로드와 텍스트 추출
- URL 본문 추출
- B팀 직무 분류 모델 결과 연결
- C팀 Ko-Sentence-BERT 기반 의미 유사도 격차 분석 결과 연결
- LLM API 기반 리포트 생성. 현재는 분석 결과를 템플릿으로 설명한다.

## 13. 하드코딩 방지 기준

제품 결과 생성 경로에서 특정 답을 박아두지 않는다.

- 역량 후보와 직무군 분류 키워드는 `backend/app/data/skill_taxonomy.json`에서 관리한다.
- 부정 표현, 필수/우대 판정, gap score 기준은 `backend/app/data/analyzer_rules.json`에서 관리한다.
- 학습자료는 코드 배열이 아니라 `backend/app/data/learning_resources.csv`에서 관리한다.
- 추천 점수는 `backend/app/services/scorer.py`에서 계산하고, 신뢰도는 `reliability / 5`로 정규화한다.
- 샘플 endpoint는 제품 API에서 제거한다. 실제 흐름은 사용자가 입력한 `/analyze` 요청만 기준으로 한다.
- 로컬 포트와 API origin은 코드 고정값이 아니라 환경변수와 Next rewrite로 연결한다.

## 14. 발표용 설명

> 사용자는 채용공고와 자신의 자소서, 이력서, 포트폴리오 자료를 입력하고 원하는 학습 기간과 난이도를 선택합니다. 시스템은 채용공고의 요구 역량과 지원자 자료의 보유 역량을 비교해 부족 역량과 부족 정도를 계산한 뒤, 직접 구축한 한국어 학습자료 DB에서 관련 자료를 검색하고 주차별 학습 로드맵과 자연어 분석 리포트를 생성합니다.
