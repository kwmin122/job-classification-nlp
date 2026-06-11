# JD 기반 역량 분석 및 학습 로드맵 추천

> 자연어처리 기말 프로젝트 — 채용공고와 지원 자료를 비교해 직무 적합도, 부족 역량, 주차별 학습 로드맵, 추천 자료를 제공하는 NLP 기반 대시보드 (v5 증거 우선 엔진)

---

## 빠른 시작

### Mac / Linux

```bash
git clone https://github.com/kwmin122/job-classification-nlp.git
cd job-classification-nlp

# 백엔드
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010

# 프론트엔드 (새 터미널)
cd frontend
npm install
cp .env.example .env.local
npm run build
npm run start -- --port 3010
```

### Windows

```powershell
git clone https://github.com/kwmin122/job-classification-nlp.git
cd job-classification-nlp

# 백엔드
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010

# 프론트엔드 (새 PowerShell 창)
cd frontend
npm install
copy .env.example .env.local
npm run build
npm run start -- --port 3010
```

브라우저에서 **http://localhost:3010** 접속

> 첫 실행 시 Ko-SRoBERTa 모델 자동 다운로드 1~3분 소요
> 서버 시작 시 모델·임베딩을 미리 로드하므로 첫 기동에 약 1분 걸린 뒤 모든 분석은 즉시 응답합니다.

> **JDK는 선택입니다.** 직무 분류 전처리에 konlpy(Okt, Java 필요)를 쓰지만, JDK가 없으면
> 자동으로 폴백 토크나이저로 동작합니다(추가 설치 없이 실행 가능). 직무 라벨 정확도를 높이려면
> [Temurin JDK 17](https://adoptium.net) 설치 후 `JAVA_HOME`을 설정하세요. fit·요구역량·
> 추천자료는 JDK 유무와 무관하게 동일합니다.

---

## v5 증거 우선 엔진

기존 키워드 매칭 방식에서 **증거(DID/SAID) 우선 분류**로 전면 교체되었습니다.

| 단계 | 설명 |
|------|------|
| `classify_sentence` | 자소서 각 문장을 DID(실제 수행) / SAID(주장·포부·이슈) / NOISE(무관)로 분류 |
| `extract_owned` | DID 문장에서 가제타어(용어집) + Ko-SRoBERTa 임베딩 폴백으로 역량 키워드 추출 |
| `score` | technical_match(기술 키워드 일치) + experience_evidence(DID 문장 근거) → fit(종합 적합도) |
| `extract_strengths` | STRENGTH_LEXICON + 티어 가중치로 보조 강점(Adjacent) 도출 |
| `build_roadmap` | 부족 역량 × 중요도 × 자료 DB → 주차별 실습 로드맵 |
| `search_resources` | 코사인 유사도 기반 RAG, resources.csv 116개 큐레이션 자료 |

### 핵심 지표

- **fit** = 0~100 (기술 매칭 × 경험 근거 가중 합산)
- **states** = `{OWNED, GAP, UNOBSERVABLE}` 세 상태로 역량 분류
- **GAP 유형** = learning(학습 부족) / evidence(근거 부족) / expression(표현 부족) / explicit(명시적 부족)

---

## 새 대시보드 UI (Ventriloc 디자인 시스템)

이전 초록 테마 대시보드에서 Ventriloc 스타일 디자인으로 완전 교체되었습니다.

| 화면 | 내용 |
|------|------|
| **분석 대시보드** | 예측 직무 + 적합도 게이지 + 점수 상세(ScorePanel) + 역량 탭(충족/부분/부족/보조) |
| **분석 리포트** | 자연어 요약 · 강점 · 부족 역량 · 표현 보완 · 추천 학습 순서 (복사/Markdown/PDF 버튼) |
| **추천 자료함** | 부족 역량별 Top 3 자료 카드, 로드맵 추가·대체·숨김 |
| **학습 로드맵** | 2/4/8/12주 토글, 각 주차 펼치기 + 완료 체크 |

**디자인 토큰**
- Signal Orange `#ff682c`, Carbon `#202020`, Mist `#efefef`, Paper `#fff`
- 폰트: Space Grotesk (CDN) / Inter (CDN) / Pretendard (CDN)
- 8px 카드 radius, 999px 필 radius, 애니메이션: spinPulse · pulse · peekIn · fadeIn · tabIn

---

## 기술 스택

| 레이어 | 내용 |
|--------|------|
| 백엔드 | Python 3.13, FastAPI, Ko-SRoBERTa (`jhgan/ko-sroberta-multitask`), TF-IDF+SVM / LSTM / TextCNN 앙상블, v5 증거 우선 엔진 |
| 프론트엔드 | Next.js 16, TypeScript, Ventriloc 디자인 시스템 |
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

### 2. Ko-SRoBERTa 모델 자동 다운로드 안내

학습된 분류기 모델 파일(`.pkl`, `.pt`)은 레포에 포함되어 있습니다. 별도 작업 불필요.

> Ko-SRoBERTa (`jhgan/ko-sroberta-multitask`) 모델은 백엔드 **첫 실행 시** HuggingFace에서 자동 다운로드됩니다 (약 430MB, 네트워크 필요, 1~3분 소요).

---

### 3. 백엔드 설정

**Mac / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010
```

정상 기동 확인:
```
INFO:     Uvicorn running on http://127.0.0.1:8010
```

---

### 4. 프론트엔드 설정

새 터미널에서:

**Mac / Linux**
```bash
cd frontend
npm install
cp .env.example .env.local
npm run build
npm run start -- --port 3010
```

**Windows (PowerShell)**
```powershell
cd frontend
npm install
copy .env.example .env.local
npm run build
npm run start -- --port 3010
```

`NEXT_PUBLIC_API_URL` 환경변수 (`frontend/.env.local`)가 백엔드 주소를 가리키도록 설정되어 있어야 합니다:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8010
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

---

## 요약: 서버 2개 동시 실행

**Mac / Linux**
```bash
# 터미널 1 — 백엔드
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010

# 터미널 2 — 프론트엔드
cd frontend && npm run start -- --port 3010
```

**Windows**
```powershell
# 터미널 1 — 백엔드
.venv\Scripts\activate
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010

# 터미널 2 — 프론트엔드
cd frontend; npm run start -- --port 3010
```

---

## 테스트

```bash
# 백엔드 단위 테스트
source .venv/bin/activate   # Windows: .venv\Scripts\activate
cd backend
python -m pytest tests/ -q
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 백엔드 `ModuleNotFoundError` | 가상환경 미활성화 | `source .venv/bin/activate` (Mac) / `.venv\Scripts\activate` (Windows) |
| 프론트 `/api/*` 404 | `.env.local` 없음 | `cp frontend/.env.example frontend/.env.local` 후 rebuild |
| 잡코리아 URL에서 빈 텍스트 | Playwright Chromium 미설치 | `npx playwright install chromium` |
| `torch` 설치 실패 | Python 버전 불일치 | Python 3.11~3.13 사용 |
| 첫 실행 느림 | Ko-SRoBERTa 다운로드 중 | 1~3분 대기 |
| UI 블록 없음 (`ui: null`) | 백엔드 v5 어댑터 오류 | 백엔드 로그에서 `adapter.py` 스택 트레이스 확인 |

---

## 프로젝트 구조

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 앱 (/analyze, /extract 엔드포인트)
│   │   ├── schemas.py                 # Pydantic 요청/응답 스키마 (ui 블록 포함)
│   │   ├── services/
│   │   │   ├── c_part_v5/             # v5 증거 우선 역량 분석 엔진
│   │   │   │   ├── engine.py          # classify_sentence / extract_owned / score
│   │   │   │   └── adapter.py        # run_c_part_analysis + _build_ui_block
│   │   │   ├── text_extractor.py      # URL/파일/Playwright 텍스트 추출
│   │   │   ├── scorer.py              # 추천 자료 점수 계산
│   │   │   └── embedding_retriever.py # RAG 추천 검색
│   │   ├── data/
│   │   │   └── resources.csv          # 큐레이션 학습 자료 DB
│   │   └── models/job_classifier/     # 학습된 분류기 모델 (.pkl, .pt)
│   └── tests/                         # 백엔드 단위 테스트
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # 메인 페이지 (input→analyzing→results 스테이지)
│   │   ├── layout.tsx                 # CDN 폰트 (Pretendard/Inter/Space Grotesk)
│   │   └── globals.css                # Ventriloc 디자인 시스템 (styles+components)
│   ├── components/
│   │   ├── Sidebar.tsx                # 사이드바 + useCountUp hook
│   │   ├── Icons.tsx                  # SVG 아이콘 팩토리
│   │   ├── InputView.tsx              # 입력 화면 (JD/자소서/옵션)
│   │   ├── AnalyzingView.tsx          # 분석 중 타임라인 애니메이션
│   │   ├── ResultsSummary.tsx         # 게이지 + 점수 상세 패널
│   │   ├── ResultsCompetency.tsx      # 역량 탭 (충족/부분/부족/보조) + 제외 섹션
│   │   └── ResultsRecos.tsx           # 추천 자료함 + 로드맵 + 리포트
│   ├── lib/
│   │   ├── api.ts                     # 백엔드 API 클라이언트
│   │   └── types.ts                   # TypeScript 타입 (UiBlock 포함)
│   └── .env.example                   # NEXT_PUBLIC_API_URL 예시
└── README.md
```

## 이미지 기반 채용공고 OCR (easyocr)

linkareer 등 일부 채용 사이트는 직무 내용을 텍스트가 아니라 **포스터 이미지**로 게시합니다.
이 경우 URL 입력 시 본문 텍스트에 직무 요구사항이 없으므로, 시스템이 페이지의 큰 이미지를
자동으로 **OCR**(easyocr)하여 실제 JD 텍스트를 복원한 뒤 분석합니다.

- 엔진: `easyocr` (PyTorch 기반, **Windows/macOS/Linux 동일 동작**, 별도 바이너리 설치 불필요).
- 최초 1회 모델 자동 다운로드(약 100MB, 네트워크 필요). 이후 오프라인 동작.
- 설치: `pip install -r backend/requirements.txt` (easyocr, pillow 포함).
- 동작 조건: URL 본문에 직무 마커(담당업무/자격요건/이런 업무 등)가 없을 때만 OCR 작동(graceful).
- 미설치 시: OCR을 건너뛰고 텍스트만으로 분석(빈 결과 대신 안내).
- 참고: OCR은 페이지 렌더링 + 인식으로 수십 초가 걸릴 수 있습니다(이미지 공고에 한함).
