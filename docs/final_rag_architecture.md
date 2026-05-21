# 최종용 D 파트 RAG 설계

Generated: 2026-05-21

## 결론

최종 제출용 D 파트는 현재 코드의 TF-IDF 검색을 그대로 최종 주장으로 삼지 않고, 한국어/영어 기술명을 함께 처리할 수 있는 로컬 임베딩 기반 RAG로 설계한다.

```text
C 파트 skill_gaps JSON
→ query text 생성
→ 학습자료 chunk embedding 검색
→ Top-K 후보 검색
→ 추천 점수 재계산
→ 로드맵 생성
→ LLM 또는 템플릿 리포트 생성
→ 로컬 대시보드 출력
```

역할 경계는 명확히 둔다.

- C 파트: 채용공고와 지원자 텍스트를 비교해 `skill_gaps`를 만든다.
- D 파트: `skill_gaps`를 입력으로 받아 학습자료 추천, 로드맵, 리포트, 대시보드를 만든다.
- D 파트는 부족 역량을 새로 판정하지 않는다.

## API 결정

### 검색/임베딩

외부 Embedding API는 사용하지 않는다.

최종 기본값:

```text
BAAI/bge-m3
```

이유:

- 한국어와 영어 기술명이 섞인 검색에 적합한 multilingual embedding 모델이다.
- Hugging Face 모델 카드 기준 multilingual, dense/sparse/ColBERT 기능을 지원한다.
- API key, 유료 호출, 네트워크 실패 없이 재현 가능하다.
- 학습자료 80개 규모에서는 CPU로도 사전 임베딩 생성이 가능하다.

### BGE-M3를 기본 모델로 고른 이유

모델 선택 기준은 "가장 최신이라서"가 아니라, 우리 D 파트의 데이터 형태와 발표 재현성에 맞는가다.

우리 검색 데이터는 일반 한국어 문장만 있는 데이터가 아니다.

```text
Docker, Spring Boot, JPA, REST API, AWS, CI/CD, React, Next.js, LangChain
```

처럼 영어 기술명과 한국어 설명이 섞여 있다. 따라서 한국어 문장 유사도 모델만으로는 부족하고, 한국어/영어 혼합 검색을 처리할 수 있는 multilingual retrieval 모델이 더 적합하다.

선택 기준:

| 기준 | 왜 필요한가 | BGE-M3 판단 |
|---|---|---|
| 한국어+영어 혼합 검색 | 채용공고와 학습자료에 영어 기술명이 많음 | 100개 이상 언어를 지원하는 multilingual 모델 |
| 검색 목적 적합성 | D 파트는 분류가 아니라 부족 역량 query로 자료를 찾는 retrieval 문제 | dense retrieval을 기본 지원 |
| 확장성 | 지금은 80개 메타데이터지만, 나중에 문서/강의 설명이 길어질 수 있음 | 최대 8192 token 입력까지 고려된 모델 |
| 구현 단순성 | 팀원이 로컬에서 재현해야 함 | `sentence-transformers`로 바로 사용 가능 |
| 비용/재현성 | 발표 당일 API key나 네트워크에 의존하면 위험 | 로컬 실행 가능 |
| 향후 개선 여지 | 시간이 남으면 hybrid search나 reranking 설명 가능 | dense, sparse, ColBERT 계열 검색 기능을 같은 모델 계열에서 설명 가능 |

즉, BGE-M3는 우리 프로젝트에서 "한국어 학습자료 추천"만 보는 모델이 아니라, "한국어 문장 + 영어 기술명 + 검색형 RAG"를 같이 처리하기 위한 기본 선택이다.

주의할 점:

- BGE-M3가 항상 모든 경우에 최고라는 뜻은 아니다.
- 우리 데이터 80개에서는 모델 성능보다 검색 구조와 추천 점수 설계가 더 중요하다.
- 그래서 최종 구현에서는 BGE-M3를 기본값으로 두되, 환경 문제가 생기면 `multilingual-e5-small`로 교체할 수 있게 한다.

### 다른 후보를 기본값으로 두지 않은 이유

| 후보 | 장점 | 기본값으로 두지 않은 이유 |
|---|---|---|
| `jhgan/ko-sroberta-multitask` | 한국어 문장 유사도에 강하고 가볍다 | 한국어 중심 모델이라 영어 기술명이 섞인 검색에는 BGE-M3보다 프로젝트 요구와 덜 맞다. 모델 카드 기준 최대 sequence length도 128로 짧다. |
| `intfloat/multilingual-e5-small` | 384차원이라 가볍고 빠르다 | fallback으로는 좋지만, 최종 발표용 기본 모델은 검색 기능과 확장성 설명이 더 좋은 BGE-M3가 낫다. |
| `text-embedding-3-small` | OpenAI의 저비용 embedding API이며 검색/추천에 적합하다 | API key, 비용, 네트워크 의존성이 생긴다. 최종 발표 환경에서는 로컬 재현성이 더 중요하다. |
| `text-embedding-3-large` | OpenAI의 더 강한 embedding API이며 다국어 성능이 좋다 | small보다 비용이 높고 API 의존성이 있다. 80개 학습자료 DB에는 과한 선택이다. |
| GPT 계열 모델 | 자연어 리포트 작성과 설명 생성에 강하다 | embedding vector를 만드는 검색 모델이 아니라 생성 모델이다. RAG 검색의 retriever로 쓰지 않고 report generator로만 쓴다. |
| TF-IDF | 빠르고 설명이 쉽다 | `Docker 배포 경험`과 `컨테이너 기반 운영 경험`처럼 표현이 달라도 의미가 비슷한 경우를 잡기 어렵다. 최종용 RAG 주장으로는 약하다. |

### OpenAI 모델과 비교

OpenAI의 `text-embedding-3` 계열은 품질과 사용성이 좋은 embedding API다. 공식 embedding guide 기준으로 `text-embedding-3-small`은 기본 1536차원, `text-embedding-3-large`는 기본 3072차원 embedding을 반환한다. 둘 다 최대 입력은 8192 token이며, `dimensions` 파라미터로 출력 차원을 줄일 수 있다.

정량 비교:

| 모델 | 실행 위치 | 기본 차원 | 최대 입력 | 비용/의존성 | 공식/문서상 특징 |
|---|---|---:|---:|---|---|
| `BAAI/bge-m3` | 로컬 | 1024 | 8192 | 무료, 모델 다운로드 필요 | 100개 이상 언어, dense/sparse/ColBERT, long document retrieval 설명 가능 |
| `intfloat/multilingual-e5-small` | 로컬 | 384 | 512 수준으로 운용 | 무료, 모델 다운로드 필요 | 100개 언어 지원, 작고 빠른 fallback |
| `text-embedding-3-small` | OpenAI API | 1536 | 8192 | 공식 문서 기준 $0.02 / 1M tokens | MTEB 62.3%, 비용 대비 강한 API 후보 |
| `text-embedding-3-large` | OpenAI API | 3072 | 8192 | 공식 문서 기준 $0.13 / 1M tokens | MTEB 64.6%, OpenAI embedding 중 고성능 후보 |
| `text-embedding-ada-002` | OpenAI API | 1536 | 8192 | 공식 문서 기준 $0.10 / 1M tokens | older embedding model, MTEB 61.0% |

이 표만 보면 `text-embedding-3-small`도 매우 좋은 선택이다. 특히 API key가 있고 발표 환경에서 인터넷이 보장된다면 구현 난이도는 OpenAI embedding API가 더 낮다. 그래도 최종 기본값을 BGE-M3로 둔 이유는 "성능만"이 아니라 "로컬 재현성, 비용 0원, 한국어+영어 기술명 혼합 검색, RAG 구조 설명 가능성"을 함께 봤기 때문이다.

| 모델 | 역할 | 장점 | 단점 | 최종 판단 |
|---|---|---|---|---|
| `BAAI/bge-m3` | 로컬 embedding retriever | 100개 이상 언어, 8192 token, dense/sparse/ColBERT 검색 설명 가능, API 비용 없음 | 로컬 설치와 모델 다운로드 필요 | 최종 기본값 |
| `text-embedding-3-small` | OpenAI embedding API | 저렴하고 빠르며 검색/추천용으로 바로 사용 가능, 1536차원 기본값 | API key와 네트워크 필요, 결과 재현이 외부 서비스에 의존 | 대안 후보. 제출 기본값은 아님 |
| `text-embedding-3-large` | OpenAI embedding API | `3-small`보다 더 강한 embedding 후보, 3072차원 기본값 | 비용이 더 높고 80개 DB에는 과함, API 의존 | 품질 비교용 후보. 기본값은 아님 |
| `text-embedding-ada-002` | OpenAI 구형 embedding API | 예전 자료가 많아 설명하기 쉬움 | 공식 문서상 older embedding model이고 `text-embedding-3-small`보다 비용 대비 선택 이유가 약함 | 제외 |
| GPT 계열 | 자연어 생성 LLM | 리포트, 요약, 한계점, 발표 문장 생성에 적합 | 검색용 embedding vector를 만드는 모델이 아님 | 선택적 report mode에서만 사용 |

정리하면, `text-embedding-3-small`을 쓰면 구현은 더 간단하고 품질도 안정적이다. 하지만 기말 프로젝트 최종 제출에서는 팀원이 같은 환경에서 재현할 수 있어야 하고, 발표 당일 API key나 네트워크 상태에 막히면 안 된다. 그래서 기본 retriever는 `BAAI/bge-m3`로 두고, 보고서에는 "`text-embedding-3-small/large`도 비교했지만 최종 기본값은 로컬 재현성을 우선했다"고 설명한다.

GPT 계열은 역할이 다르다. GPT는 추천 자료를 검색하는 retriever가 아니라, 이미 계산된 `skill_gaps`, 추천 자료, 로드맵을 사람이 읽기 좋은 문장으로 바꾸는 generator다. 따라서 최종 시스템에서 GPT를 쓰더라도 아래 위치에만 둔다.

```text
retriever: BGE-M3 또는 text-embedding-3 계열
generator: template 기본, GPT API 선택
```

Fallback:

```text
intfloat/multilingual-e5-small
```

이유:

- 더 가볍고 빠르다.
- 384차원 embedding이라 CPU 실행이 쉽다.
- 최종 발표 직전 환경 문제가 생기면 안정적인 대체 모델로 쓴다.

### LLM 리포트 생성

LLM API는 필수 의존성으로 두지 않는다.

최종 구조:

```text
ReportGenerator
├─ template mode: 기본값, API key 없음
└─ llm mode: 선택, API key 있을 때만 사용
```

기본 제출은 `template mode`로도 완성 가능해야 한다.
LLM API를 붙이면 판단을 새로 시키는 용도가 아니라, 이미 계산된 결과를 자연어로 정리하는 용도로만 사용한다.

선택 API 후보:

| API | 사용 목적 | 최종 판단 |
|---|---|---|
| OpenAI/Gemini/Claude | 자연어 리포트 문장화 | 선택 |
| OpenAI `text-embedding-3-small/large` 등 외부 embedding API | 자료 검색 임베딩 | 기술적으로 가능하지만 최종 기본값은 아님 |

즉, RAG 검색 품질은 로컬 embedding으로 만들고, LLM API는 있으면 리포트 문장만 다듬는 옵션으로 둔다.

## 왜 외부 Embedding API를 안 쓰는가

기말 프로젝트 최종 제출에서는 재현성이 중요하다.

외부 API를 쓰면 다음 문제가 생긴다.

- API key 필요
- 호출 비용 발생 가능
- 발표 당일 네트워크/API 제한 리스크
- 팀원이 같은 결과를 재현하기 어려움

반대로 로컬 임베딩은 한 번 설치하면 같은 CSV에서 같은 결과를 낼 수 있다.

## 청킹 설계

현재 RAG DB는 긴 PDF 문서가 아니라 학습자료 메타데이터 DB다. 따라서 일반 문서형 RAG처럼 500자 단위로 자르는 방식은 맞지 않다.

최종 청킹 기준:

```text
CSV 1행 = chunk 1개
```

각 chunk는 하나의 학습자료를 의미한다.

```json
{
  "chunk_id": "BE009",
  "resource_id": "BE009",
  "job_group": "백엔드 개발자",
  "skill": "Docker",
  "sub_skill": "컨테이너",
  "type": "강의",
  "level": "beginner",
  "language": "한국어",
  "text": "백엔드 개발자 Docker 컨테이너 인프런 Docker 강의 모음 Docker 컨테이너와 백엔드 배포 강의를 한국어로 찾아 학습한다 Docker CI CD 환경 경험 요구 대응"
}
```

### chunk text 구성

임베딩에 넣는 텍스트:

```text
job_group + skill + sub_skill + title + description + reason
```

포함하지 않는 필드:

- URL
- estimated_time
- free_or_paid

이 필드는 검색 의미에는 약하고, 추천 결과 표시용 metadata로만 쓴다.

긴 PDF나 강의 전문을 직접 넣는 구조로 확장하면 그때는 500~800자 단위 청킹을 검토한다. 현재 최종 제출 범위는 메타데이터 기반 80개 학습자료 DB이므로 1행 1chunk가 맞다.

## Query 설계

C 파트가 넘기는 부족 역량 1개마다 query를 만든다.

입력:

```json
{
  "predicted_job": "백엔드 개발자",
  "skill": "Docker",
  "gap_score": 82,
  "gap_level": "높음",
  "importance": "필수",
  "evidence": "JD에는 Docker 기반 배포 경험이 요구되지만 지원자 텍스트에는 컨테이너 기반 배포 경험이 나타나지 않음"
}
```

query text:

```text
백엔드 개발자 필수 부족 역량 Docker
JD 요구사항과 지원자 근거: JD에는 Docker 기반 배포 경험이 요구되지만 지원자 텍스트에는 컨테이너 기반 배포 경험이 나타나지 않음
한국어 학습자료 추천
```

## 임베딩 저장 설계

최종 구조:

```text
backend/app/data/learning_resources.csv
backend/app/cache/resource_embeddings.npz
backend/app/cache/resource_index_meta.json
```

저장 내용:

- `resource_embeddings.npz`: normalized dense embedding matrix
- `resource_index_meta.json`: embedding 순서와 resource id 매핑

DB가 80개라서 Chroma 같은 별도 서버형 vector DB는 필요 없다.

선택지:

| 방식 | 최종 판단 |
|---|---|
| numpy matrix | 기본값 |
| FAISS | 선택, 검색 최적화 필요할 때 |
| Chroma | 과함 |
| SQLite VSS | 과함 |

최종 제출은 `numpy matrix + cosine similarity`로 충분하다.
FAISS는 시간이 남으면 붙인다.

## 검색 점수 설계

기존 점수 공식을 유지하되, `semantic_similarity`만 TF-IDF에서 dense embedding cosine similarity로 교체한다.

```text
recommend_score =
100 * (
  0.60 * dense_similarity
+ 0.20 * skill_match
+ 0.10 * job_group_match
+ 0.10 * reliability_norm
)
```

정규화:

- `dense_similarity`: cosine similarity를 0~1 범위로 변환
- `skill_match`: skill 또는 sub_skill 직접 매칭이면 1, 아니면 0
- `job_group_match`: 예측 직무군과 자료 직무군이 같으면 1, 아니면 0
- `reliability_norm`: reliability / 5

## 검색 절차

부족 역량마다 다음 순서로 검색한다.

```text
1. query embedding 생성
2. 전체 80개 chunk와 cosine similarity 계산
3. dense similarity 기준 Top-10 후보 추출
4. skill/job_group/reliability를 반영해 recommend_score 재계산
5. skill_match가 있는 자료를 우선 선택
6. Top-K 추천 자료 반환
```

최종 기본값:

```text
top_k = 3
candidate_k = 10
```

## 로드맵 생성 설계

로드맵은 LLM이 임의로 판단하지 않는다. `gap_score`, `gap_level`, `importance`, 추천 자료를 기반으로 규칙적으로 생성한다.

우선순위:

```text
gap_score 높은 순
필수 > 우대
job_group_match 있는 자료 우선
```

단계:

```text
1. 개념 이해
2. 한국어 자료 1~2개 학습
3. 작은 실습
4. 기존 포트폴리오에 적용
5. README/면접 답변 근거 정리
```

## 리포트 생성 설계

LLM을 사용할 경우 프롬프트는 아래 원칙을 지킨다.

- C 파트가 준 `skill_gaps`를 사실로 취급한다.
- LLM이 부족 역량을 새로 판단하지 않는다.
- 추천 자료 목록 밖의 자료를 지어내지 않는다.
- gap_score와 evidence를 반드시 언급한다.
- 마지막에 한계점을 적는다.

프롬프트 입력:

```json
{
  "predicted_job": "...",
  "fit_score": 72,
  "matched_skills": ["..."],
  "skill_recommendations": [...],
  "roadmap": [...]
}
```

출력:

```text
1. 전체 요약
2. 가장 먼저 보완할 역량
3. 부족 정도와 근거
4. 추천 학습 순서
5. 추천 자료
6. 실습 프로젝트
7. 한계점
```

## C 파트 연결 계약

C는 반드시 아래 형식으로 넘긴다.

```json
{
  "predicted_job": "백엔드 개발자",
  "fit_score": 72,
  "matched_skills": ["Java", "Spring Boot", "MySQL"],
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

`missing_skills`만 넘기는 방식은 최종 계약에서 받지 않는다.
이유는 D 파트가 학습 우선순위를 만들려면 `gap_score`, `importance`, `evidence`가 필요하기 때문이다.

## 최종 구현 단계

### Step 1. Embedding retriever 추가

새 파일:

```text
backend/app/services/embedding_retriever.py
```

역할:

- CSV row를 chunk text로 변환
- embedding 생성
- cache 저장/로드
- cosine similarity 검색

### Step 2. 기존 TfidfRetriever를 fallback으로 유지

```text
retriever_mode = embedding | tfidf
```

최종 기본값은 `embedding`.

### Step 3. requirements 추가

```text
sentence-transformers
torch
numpy
```

선택:

```text
faiss-cpu
```

### Step 4. API 응답에 검색 방식 표시

응답에 아래 필드를 추가한다.

```json
{
  "retrieval_mode": "embedding",
  "embedding_model": "BAAI/bge-m3",
  "chunking_strategy": "one_resource_row_per_chunk"
}
```

### Step 5. 검증

필수 검증:

```bash
PYTHONPATH=backend .venv/bin/python -m compileall backend/app backend/tools
PYTHONPATH=backend .venv/bin/python backend/tools/verify_resource_urls.py
PYTHONPATH=backend .venv/bin/python backend/tools/build_embeddings.py
curl -X POST http://127.0.0.1:8000/recommend?top_k=3 ...
cd frontend && npm run build
```

## 발표에서 말할 문장

> 최종 시스템에서는 학습자료 DB의 각 행을 하나의 chunk로 보고, 직무군, 부족 역량, 자료 설명, 선정 이유를 합쳐 임베딩합니다. C 파트가 넘긴 부족 역량과 근거 문장도 query로 임베딩한 뒤, cosine similarity로 관련 자료를 검색합니다. 이후 기술명 직접 매칭, 직무군 일치, 자료 신뢰도를 함께 반영해 최종 추천 점수를 계산합니다. 이 구조는 웹 전체 검색 RAG가 아니라, 잡코리아 요구역량 기반으로 만든 한국어 학습자료 DB에 대한 추천형 RAG입니다.

## 현재 구현과 최종 설계 차이

| 항목 | 현재 구현 | 최종 설계 |
|---|---|---|
| 검색 방식 | TF-IDF cosine | BGE-M3 dense embedding cosine |
| 청킹 | CSV 1행 | CSV 1행 유지 |
| 벡터 저장 | 없음 | `.npz` cache |
| 벡터 DB | 없음 | numpy 기본, FAISS 선택 |
| LLM 리포트 | 템플릿 | 템플릿 기본, LLM API 선택 |
| 외부 API 의존 | 없음 | 없음, LLM만 선택 |
| 재현성 | 높음 | 높음 |

## 참고 근거

- BAAI/bge-m3 Hugging Face model card: https://huggingface.co/BAAI/bge-m3
- intfloat/multilingual-e5-small Hugging Face model card: https://huggingface.co/intfloat/multilingual-e5-small
- Sentence Transformers documentation: https://www.sbert.net/
- OpenAI embeddings guide: https://platform.openai.com/docs/guides/embeddings
- OpenAI text-embedding-3-small model page: https://platform.openai.com/docs/models/text-embedding-3-small
- OpenAI text-embedding-3-large model page: https://platform.openai.com/docs/models/text-embedding-3-large
- OpenAI models guide: https://developers.openai.com/api/docs/models
