# JD 기반 역량 분석 및 학습 로드맵 추천

> 자연어처리 기말 프로젝트 — 채용공고와 지원 자료를 비교해 직무 적합도, 부족 역량, 주차별 학습 로드맵, 추천 자료를 제공하는 NLP 기반 대시보드

---

## 기술 스택

| 레이어 | 내용 |
|--------|------|
| 백엔드 | Python 3.13, FastAPI, Ko-SRoBERTa (`jhgan/ko-sroberta-multitask`), TF-IDF+SVM / LSTM / TextCNN 앙상블 |
| 프론트엔드 | Next.js 16, TypeScript, Recharts |
| 동적 추출 | Node.js + Playwright Chromium (잡코리아 JS 렌더링 공고 대응) |
| 추천 검색 | 코사인 유사도 (로컬) / OpenAI text-embedding-3-small (선택) |

---

## 팀원 설치 및 실행 가이드

### 0. 사전 요구사항

```bash
python3 --version   # 3.11 이상 (3.13 권장)
node --version      # 18 이상
```

---

### 1. 레포 클론

```bash
git clone https://github.com/kwmin122/job-classification-nlp.git
cd job-classification-nlp
```

---

### 2. 모델 파일 배치

학습된 분류기 모델 파일은 용량 문제로 Git에 포함되지 않습니다.
팀 공유 드라이브에서 `models.zip`을 받아 아래 경로에 압축 해제하세요.

```
backend/app/models/
└── job_classifier/
    ├── model_tfidf_svm.pkl
    ├── model_lstm.pt
    ├── model_textcnn.pt
    ├── model_lstm_fasttext.pt
    └── preprocessed_data.pkl
```

> Ko-SRoBERTa 모델은 첫 실행 시 HuggingFace에서 자동 다운로드됩니다 (약 430MB).

---

### 3. 백엔드 설정

```bash
# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 패키지 설치 (torch 포함, 3~10분 소요)
pip install -r backend/requirements.txt

# 백엔드 서버 실행
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010
```

정상 기동 확인:
```
INFO:     Uvicorn running on http://127.0.0.1:8010
```

---

### 4. 프론트엔드 설정

새 터미널에서:

```bash
cd frontend

# 의존성 설치
npm install

# 환경변수 파일 생성
cp .env.example .env.local
# .env.local 내용: BACKEND_ORIGIN=http://127.0.0.1:8010

# 빌드 및 실행
npm run build
npm run start -- --port 3010
```

브라우저에서 **http://localhost:3010** 접속.

---

### 5. (선택) Playwright Chromium 설치

잡코리아 등 JS 렌더링 공고의 자동 추출 기능에 필요합니다.

```bash
npx playwright install chromium
```

이미 `~/.cache/ms-playwright/chromium-*`가 있으면 생략 가능.

---

### 6. (선택) OpenAI API Key

API Key 없이도 로컬 Ko-SRoBERTa 임베딩으로 분석 가능합니다.
Key 입력 시 `text-embedding-3-small`을 사용해 추천 자료 정확도가 향상됩니다.
대시보드 하단 **API Key** 필드에 입력.

---

## 요약: 서버 2개 동시 실행

```bash
# 터미널 1 — 백엔드 (프로젝트 루트)
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010

# 터미널 2 — 프론트엔드 (frontend/ 디렉토리)
npm run start -- --port 3010
```

---

## 테스트

```bash
# 백엔드 단위 테스트 (87개)
source .venv/bin/activate
PYTHONPATH=backend python -m unittest discover -s backend/tests

# E2E 테스트 (서버 2개 실행 중이어야 함)
cd frontend && npm run e2e
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 백엔드 `ModuleNotFoundError` | 가상환경 미활성화 | `source .venv/bin/activate` |
| 프론트 `/api/*` 404 | `.env.local` 없음 | `cp frontend/.env.example frontend/.env.local` 후 rebuild |
| 잡코리아 URL에서 빈 텍스트 | Playwright Chromium 미설치 | `npx playwright install chromium` |
| `torch` 설치 실패 | Python 버전 불일치 | Python 3.11~3.13 사용 |
| 첫 실행 느림 | Ko-SRoBERTa 다운로드 중 | 1~3분 대기 |

---

## 프로젝트 구조

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 앱 (/analyze, /extract 엔드포인트)
│   │   ├── schemas.py                 # Pydantic 요청/응답 스키마
│   │   ├── services/
│   │   │   ├── c_part/                # Ko-SRoBERTa 역량 분석 파이프라인
│   │   │   ├── text_extractor.py      # URL/파일/Playwright 텍스트 추출
│   │   │   ├── scorer.py              # 추천 자료 점수 계산
│   │   │   ├── roadmap_generator.py   # 주차별 로드맵 생성 (강도×수준 매트릭스)
│   │   │   └── embedding_retriever.py # RAG 추천 검색
│   │   ├── data/
│   │   │   └── learning_resources.csv # 큐레이션 학습 자료 DB (116개)
│   │   └── models/job_classifier/     # ⚠️ Git 미포함 — 팀원 전달 필요
│   ├── tests/                         # 백엔드 단위 테스트 (87개)
│   └── tools/
│       └── playwright_extract.cjs     # Node.js Playwright 동적 추출 스크립트
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # SetupPage + DashboardPage
│   │   └── globals.css                # 디자인 시스템
│   ├── components/                    # 입력 패널 컴포넌트들
│   ├── lib/
│   │   ├── api.ts                     # 백엔드 API 클라이언트
│   │   └── types.ts                   # TypeScript 타입
│   ├── e2e/                           # Playwright E2E 테스트
│   └── .env.example                   # 환경변수 예시 → .env.local로 복사
└── README.md
```
