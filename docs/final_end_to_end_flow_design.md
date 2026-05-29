# 최종 전체 플로우 설계도

Generated: 2026-05-28  
Status: Final target architecture  
Principle: 우회 없이 모든 입력을 같은 분석 기준으로 통과시킨다.

## 1. 한 줄 정의

사용자가 채용공고와 자기 지원 자료를 URL, 텍스트, PDF, TXT 중 어떤 방식으로 넣어도, 시스템은 먼저 신뢰 가능한 텍스트로 추출하고 사용자가 확인한 뒤, A/B 직무 분류, C 역량 격차 분석, D RAG 학습자료 추천, 로드맵과 리포트 생성을 하나의 일관된 파이프라인으로 수행한다.

## 2. 최종 사용자 플로우

```text
1. 사용자가 지원할 채용공고 입력
   - 채용공고 URL
   - 채용공고 본문 텍스트
   - 채용공고 PDF/TXT 파일

2. 사용자가 자기 지원 자료 입력
   - 자소서 텍스트
   - 이력서 PDF/TXT 파일
   - 포트폴리오/README 텍스트
   - 프로젝트 설명 텍스트

3. 시스템이 원천 자료에서 텍스트 추출
   - URL HTML 본문 추출
   - PDF 텍스트 추출
   - TXT 인코딩 처리
   - 직접 입력 텍스트 정리

4. 사용자가 추출된 텍스트 확인 및 수정
   - 채용공고 추출 결과 확인
   - 지원자 자료 추출 결과 확인
   - 잘못 추출된 부분 직접 수정

5. 사용자가 학습 목표 설정
   - 기간: 2주, 4주, 8주, 12주
   - 현재 수준: 입문, 기초, 실무, 심화
   - 강도: 가볍게, 보통, 집중
   - 선택: OpenAI API Key 입력

6. 분석 시작
   - A/B 앙상블 직무 분류
   - C 요구 역량/보유 역량/부족 역량 분석
   - D 부족 역량 기반 학습자료 검색
   - 주차별 로드맵 생성
   - 자연어 분석 리포트 생성

7. 결과 확인
   - 예측 직무
   - 직무 적합도
   - 공고 요구 역량
   - 내 보유 역량
   - 일부 보완 필요 역량
   - 부족 역량과 gap score
   - 근거 문장
   - 추천 학습자료
   - 주차별 로드맵
   - 분석 리포트
```

## 3. 전체 시스템 설계도

```text
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  Job source input        Candidate source input              │
│  URL / Text / PDF / TXT  Text / PDF / TXT / Portfolio        │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────┐   ┌─────────────────────────────┐
│  Source Extraction API     │   │  Source Extraction API       │
│  /extract/job-posting      │   │  /extract/candidate-material │
└───────────────┬───────────┘   └───────────────┬─────────────┘
                │                               │
                ▼                               ▼
┌───────────────────────────┐   ┌─────────────────────────────┐
│  Normalized Job Text       │   │  Normalized Candidate Text   │
│  source, text, warnings    │   │  label, text, warnings       │
└───────────────┬───────────┘   └───────────────┬─────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    User Preview / Edit                       │
│  추출된 텍스트를 보여주고 사용자가 분석 전 수정 가능             │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                         /analyze                             │
│  canonical text payload only                                 │
│  job_text + candidate_texts + roadmap_preferences + api_key  │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    A/B Job Classifier                        │
│  TF-IDF+SVM 0.1 + LSTM 0.5 + Text-CNN 0.3 + FastText LSTM 0.1 │
│  output: job_label, predicted_job, probabilities             │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    C Skill Gap Analyzer                      │
│  input: job_label, job_text, candidate_text                  │
│  output: required_skills, owned_skills, partial_skills, gaps │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    D RAG Recommendation                      │
│  input: skill_gaps first, partial_skills second              │
│  search target: curated learning_resources.csv               │
│  embedding: OpenAI -> BGE-M3 -> TF-IDF fallback              │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Roadmap / Report Generator                   │
│  duration + difficulty + intensity 반영                       │
│  output: weekly_roadmap, resources, report                   │
└───────────────────────────────┬─────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        Dashboard                             │
│  fit score, evidence, gaps, resources, roadmap, report       │
└─────────────────────────────────────────────────────────────┘
```

## 4. 핵심 원칙

### 4.1 파일과 URL은 분석 코어로 바로 들어가지 않는다

PDF, TXT, URL, 직접 입력은 모두 먼저 `NormalizedText`로 변환한다. `/analyze`는 원본 파일이나 URL을 직접 분석하지 않는다. 이렇게 해야 입력 방식이 달라도 A/B/C/D 분석 기준이 흔들리지 않는다.

### 4.2 추출 결과는 반드시 사용자가 확인한다

PDF 텍스트 추출은 줄바꿈, 표, 특수문자가 깨질 수 있다. 채용공고 URL은 사이트 구조나 차단 때문에 본문 추출이 실패할 수 있다. 따라서 추출된 텍스트를 바로 분석하지 않고, 사용자가 확인하고 수정할 수 있는 preview 단계를 둔다.

### 4.3 A/B/C/D는 사용자 화면의 용어가 아니다

사용자 화면에서는 다음처럼 표시한다.

| 내부 단계 | 사용자 화면 표현 |
|---|---|
| A/B 앙상블 | 직무 분류 |
| C 파이프라인 | 역량 격차 분석 |
| D RAG | 학습자료 추천 |
| gap_score | 부족 정도 |

### 4.4 D는 부족 역량을 새로 판단하지 않는다

D는 C가 반환한 `skill_gaps`와 `partial_skills`를 추천 대상으로 사용한다. 부족 여부 판단은 C의 책임이고, D는 학습자료 검색, 추천 점수 계산, 로드맵, 리포트 생성을 담당한다.

### 4.5 RAG는 큐레이션 학습자료 DB 검색이다

이 프로젝트의 RAG는 웹 전체 검색이 아니다. `learning_resources.csv`에 정리된 공식문서, 강의, 유튜브, 블로그, 책 등 학습자료 메타데이터를 대상으로 의미 기반 검색을 수행한다.

## 5. 데이터 계약

### 5.1 원천 입력

```json
{
  "kind": "job_posting",
  "source_type": "url",
  "url": "https://example.com/job",
  "text": "",
  "file_name": null,
  "file_content_type": null
}
```

```json
{
  "kind": "candidate_material",
  "source_type": "file",
  "label": "이력서",
  "file_name": "resume.pdf",
  "file_content_type": "application/pdf"
}
```

### 5.2 추출 결과

```json
{
  "source_type": "pdf",
  "label": "이력서",
  "text": "추출된 지원자 자료 텍스트",
  "char_count": 2840,
  "warnings": [
    "일부 표 구조는 줄 단위 텍스트로 변환되었습니다."
  ]
}
```

### 5.3 분석 요청

`/analyze`는 추출 완료된 텍스트만 받는다.

```json
{
  "job_posting": {
    "source_type": "text",
    "url": "https://example.com/job",
    "text": "사용자가 확인한 채용공고 텍스트"
  },
  "candidate_materials": [
    {
      "source_type": "text",
      "label": "자소서",
      "text": "사용자가 확인한 자소서 텍스트"
    },
    {
      "source_type": "text",
      "label": "이력서",
      "text": "사용자가 확인한 이력서 텍스트"
    }
  ],
  "roadmap_preferences": {
    "duration_weeks": 4,
    "difficulty": "기초",
    "intensity": "보통"
  },
  "openai_api_key": "optional request-only key"
}
```

### 5.4 분석 응답

```json
{
  "predicted_job": "백엔드 개발자",
  "job_label": "backend",
  "fit_score": 62,
  "required_skills": [],
  "owned_skills": [],
  "partial_skills": [],
  "missing_skills": [],
  "recommended_resources": [],
  "weekly_roadmap": [],
  "report": "분석 리포트",
  "retrieval_mode": "embedding",
  "embedding_model": "text-embedding-3-small"
}
```

## 6. API 설계

### 6.1 `POST /extract/job-posting`

채용공고 URL, 텍스트, PDF, TXT를 받아 분석 가능한 텍스트로 변환한다.

Input:

```text
multipart/form-data 또는 JSON
source_type: url | text | file
url?: string
text?: string
file?: UploadFile
```

Output:

```json
{
  "kind": "job_posting",
  "source_type": "url",
  "text": "추출된 채용공고 텍스트",
  "char_count": 3952,
  "warnings": [],
  "extractor": "trafilatura"
}
```

### 6.2 `POST /extract/candidate-material`

지원자 자료 텍스트, PDF, TXT를 받아 분석 가능한 텍스트로 변환한다.

Input:

```text
multipart/form-data 또는 JSON
source_type: text | file
label: 자소서 | 이력서 | 포트폴리오 | README | 기타
text?: string
file?: UploadFile
```

Output:

```json
{
  "kind": "candidate_material",
  "label": "이력서",
  "source_type": "pdf",
  "text": "추출된 이력서 텍스트",
  "char_count": 2210,
  "warnings": [],
  "extractor": "pypdf"
}
```

### 6.3 `POST /analyze`

추출 및 확인이 끝난 텍스트를 받아 전체 분석을 수행한다.

역할:

```text
canonical text payload
        ↓
A/B job classification
        ↓
C skill gap analysis
        ↓
D RAG recommendation
        ↓
roadmap/report/dashboard response
```

## 7. 추출 계층 설계

### 7.1 PDF

우선순위:

1. `pypdf`로 텍스트 추출
2. 페이지별 텍스트 병합
3. 공백, 줄바꿈, 반복 머리말/꼬리말 정리
4. 추출 텍스트가 너무 짧으면 실패로 처리

OCR은 이번 범위에서 제외한다. 스캔 PDF는 텍스트 추출 실패로 안내하고, 사용자가 직접 텍스트를 붙여넣도록 한다.

### 7.2 TXT

우선순위:

1. UTF-8 디코딩
2. 실패 시 CP949 디코딩
3. 실패 시 명확한 오류 반환
4. 공백 정리

### 7.3 URL

우선순위:

1. `httpx`로 HTML 가져오기
2. `trafilatura` 또는 `BeautifulSoup`로 본문 추출
3. script, style, nav, footer 제거
4. 채용공고 본문 길이가 너무 짧으면 실패
5. 실패 시 사용자가 공고 본문을 직접 붙여넣도록 안내

동적 렌더링, 로그인 필요, 크롤링 차단은 우회하지 않는다. 최종 제품에서는 실패를 정직하게 보여준다.

## 8. 분석 계층 상세

### 8.1 직무 분류

현재 팀 기준의 A/B 앙상블을 사용한다.

```text
final_proba =
0.1 * TF-IDF+SVM
+ 0.5 * LSTM
+ 0.3 * Text-CNN
+ 0.1 * FastText LSTM
```

라벨:

| index | label | display |
|---:|---|---|
| 0 | ai | AI/ML 엔지니어 |
| 1 | backend | 백엔드 개발자 |
| 2 | data_analyst | 데이터 분석가 |
| 3 | frontend | 프론트엔드 개발자 |

### 8.2 역량 격차 분석

입력:

```text
job_label
job_text
candidate_text
```

출력:

```text
required_skills: 채용공고에서 요구한 역량
owned_skills: 지원자 자료에서 충분히 확인된 역량
partial_skills: 일부 근거는 있으나 기준 미달인 역량
skill_gaps: 근거가 없거나 크게 부족한 역량
fit_score: 전체 적합도
evidence: 판단 근거 문장
```

판단 책임:

| 판단 | 담당 |
|---|---|
| 직무군 판단 | A/B |
| 요구 역량 추출 | C |
| 보유 역량 추출 | C |
| 부족 정도 계산 | C |
| 학습자료 추천 | D |
| 로드맵 생성 | D |
| 리포트 문장화 | D |

### 8.3 RAG 추천

검색 대상:

```text
backend/app/data/learning_resources.csv
```

추천 대상 우선순위:

```text
1순위: skill_gaps
2순위: partial_skills
제외: owned_skills
```

검색 query:

```text
predicted_job + skill + gap_level + importance + evidence
```

추천 점수:

```text
100 * (
  0.55 * semantic_similarity
+ 0.20 * skill_match
+ 0.10 * job_group_match
+ 0.10 * difficulty_match
+ 0.05 * reliability_norm
)
```

임베딩 우선순위:

```text
1. OpenAI text-embedding-3-small
2. jhgan/ko-sroberta-multitask
3. TF-IDF last resort
```

## 9. 프론트 화면 설계

### 9.1 입력 화면

```text
상단: JD Fit Dashboard

왼쪽 입력 레일
  1. 지원할 채용공고
     - 탭: URL / 텍스트 / PDF/TXT
     - 추출 결과 미리보기

  2. 내 지원 자료
     - 탭: 텍스트 / PDF/TXT
     - 자료 label 선택: 자소서, 이력서, 포트폴리오, README, 기타
     - 여러 자료 추가 가능

  3. 학습 목표
     - 기간
     - 현재 수준
     - 강도

  4. 고급 분석 설정
     - OpenAI API Key
     - 저장하지 않음 안내

  5. 분석 시작
```

### 9.2 추출 미리보기

```text
추출 성공:
  - 추출된 글자 수
  - 사용된 extractor
  - warnings
  - 수정 가능한 textarea

추출 실패:
  - 실패 원인
  - 직접 붙여넣기 fallback 안내
```

### 9.3 결과 화면

```text
요약
  - 예측 직무
  - 적합도
  - 부족 역량 개수
  - 보완 필요 개수

근거 분석
  - 공고 요구 역량
  - 보유 역량
  - 보완 필요
  - 부족 역량

Gap Matrix
  - skill
  - gap_score
  - gap_level
  - importance
  - evidence

추천 자료
  - 역량별 Top-K 자료
  - 유형, 난이도, 신뢰도, 추천 점수
  - 링크

주차별 로드맵
  - week
  - goal
  - resources
  - practice

리포트
  - 자연어 요약
  - 한계 및 주의점

방법 공개
  - retrieval_mode
  - embedding_model
  - RAG scope
  - scoring formula
```

## 10. 오류 처리 정책

| 상황 | 처리 |
|---|---|
| 채용공고 텍스트 20자 미만 | 분석 시작 비활성화 또는 오류 |
| 지원자 자료 텍스트 20자 미만 | 분석 시작 비활성화 또는 오류 |
| PDF 텍스트 추출 실패 | 직접 붙여넣기 안내 |
| URL 본문 추출 실패 | 직접 붙여넣기 안내 |
| OpenAI API Key 오류 | 로컬 임베딩으로 fallback, 사용 방식 표시 |
| BGE-M3 로딩 실패 | TF-IDF last resort 표시 |
| C 분석 실패 | 분석 실패 원인 표시, 추천 단계 실행 안 함 |
| 학습자료 DB 매칭 부족 | 낮은 신뢰도 안내와 함께 가능한 자료 표시 |

## 11. 구현 순서

### Phase 1: Source Extraction Layer

목표:

```text
PDF/TXT/URL → NormalizedText
```

해야 할 일:

- `ExtractedText` schema 추가
- `/extract/job-posting` 추가
- `/extract/candidate-material` 추가
- PDF 추출기 추가
- TXT 추출기 추가
- URL 본문 추출기 추가
- 추출 실패 테스트 추가

### Phase 2: Frontend Input Adapter

목표:

```text
사용자가 URL/PDF/TXT를 넣으면 추출된 텍스트를 확인하고 수정 가능
```

해야 할 일:

- 채용공고 입력 탭 추가
- 지원자 자료 입력 탭 추가
- 파일 업로드 UI 추가
- URL 추출 UI 추가
- 추출 미리보기 UI 추가
- 여러 지원자 자료 관리

### Phase 3: Canonical Analyze Contract

목표:

```text
모든 입력 방식이 같은 /analyze payload로 들어가게 고정
```

해야 할 일:

- `/analyze`는 텍스트만 받는 코어 API로 유지
- source provenance를 response에 남길지 결정
- 분석 전에 normalized text length 검증
- 파일/URL 직접 분석 경로 제거

### Phase 4: End-to-End Verification

목표:

```text
텍스트, PDF, TXT, URL 입력이 모두 같은 분석 결과 구조로 이어짐
```

테스트:

- 텍스트 채용공고 + 텍스트 자소서
- PDF 채용공고 + 텍스트 자소서
- URL 채용공고 + PDF 이력서
- TXT 채용공고 + TXT 지원자료
- URL 추출 실패 후 직접 붙여넣기
- OpenAI API Key 없음
- OpenAI API Key 잘못됨

## 12. 완료 기준

최종 완료는 다음을 모두 만족해야 한다.

- 사용자가 채용공고 URL을 넣어 텍스트 추출 결과를 볼 수 있다.
- 사용자가 채용공고 PDF/TXT를 올려 텍스트 추출 결과를 볼 수 있다.
- 사용자가 지원자 PDF/TXT를 올려 텍스트 추출 결과를 볼 수 있다.
- 사용자가 추출된 텍스트를 수정할 수 있다.
- 수정된 텍스트가 `/analyze`로 들어간다.
- A/B 앙상블 직무 분류가 실행된다.
- C 역량 격차 분석이 실행된다.
- D RAG 추천이 실행된다.
- 로드맵과 리포트가 화면에 표시된다.
- 각 단계 실패가 사용자에게 명확히 표시된다.
- mock, hardcoding, 샘플 자동 입력 없이 실제 입력으로 동작한다.

## 13. 현재 구현과의 차이

| 항목 | 현재 | 최종 |
|---|---|---|
| 채용공고 텍스트 입력 | 가능 | 가능 |
| 지원자 텍스트 입력 | 가능 | 가능 |
| PDF 업로드 | 없음 | 필수 |
| TXT 업로드 | 없음 | 필수 |
| 채용공고 URL | UI/로직 없음 | 필수 |
| 추출 미리보기 | 없음 | 필수 |
| A/B 직무 분류 | 연결됨 | 유지 |
| C 격차 분석 | 연결됨 | 유지 |
| D RAG 추천 | 연결됨 | 유지 |
| OpenAI API Key | 요청 단위 전달 | 유지 |

## 14. 최종 결론

근본 구조는 다음 한 문장으로 고정한다.

```text
원천 입력은 다양하게 받되, 분석 코어는 항상 사용자가 확인한 정규화 텍스트만 받는다.
```

이 구조를 지켜야 PDF, TXT, URL, 직접 입력이 모두 같은 기준으로 분석되고, A/B/C/D 파이프라인이 흔들리지 않는다.
