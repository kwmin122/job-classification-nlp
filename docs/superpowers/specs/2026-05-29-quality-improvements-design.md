# 품질 개선 설계 — C-파트 정밀도 · OCR · UX · 문서

**날짜**: 2026-05-29  
**범위**: 순수 개선 — 백엔드 API 계약 변경 없음

---

## 개요

4가지 독립 개선 항목. 우선순위 순.

| # | 항목 | 위험도 | 파일 |
|---|------|--------|------|
| 1 | C-파트 required_skills 과다 추출 수정 | 중 | `pipeline.py`, `skill_taxonomy.json`, `analyzer_rules.json` |
| 2 | PDF OCR 파이프라인 추가 | 중 | `text_extractor.py`, `requirements.txt` |
| 3 | JD/지원자 입력 UX 기본값 변경 | 저 | `frontend/app/page.tsx`, `JobPostingInputPanel.tsx` |
| 4 | 문서 동기화 (BAAI/bge-m3 레퍼런스 제거) | 저 | `docs/` |

---

## 1. C-파트 required_skills 과다 추출 수정

### 문제

`extract_required_skills()`에서 `jd_extract` 임계값이 0.28로 극히 낮아,
JD에 명시되지 않은 기술이 taxonomy의 모든 백엔드 스킬과 의미론적으로
"충분히 유사"한 것으로 판정된다.

예) `"Spring Boot REST API"` 문장 → Java(0.40), OpenAPI(0.38), Kotlin(0.35),
    Node.js(0.31), PostgreSQL(0.29) 모두 0.28 초과 → 전부 required_skills에 추가

### 설계 결정: 접근법 C (keyword-first + 높은 semantic fallback)

**변경 1 — Korean aliases 추가** (`skill_taxonomy.json` → `aliases` 객체)

아래 항목 추가. 잡코리아/사람인 등 한국어 공고의 기술명 변형을 커버한다.

```json
"스프링 부트":   "Spring Boot",
"스프링":        "Spring Boot",
"자바":          "Java",
"도커":          "Docker",
"쿠버네티스":    "Kubernetes",
"카프카":        "Kafka",
"레디스":        "Redis",
"깃":            "Git",
"파이썬":        "Python",
"텐서플로우":    "TensorFlow",
"파이토치":      "PyTorch",
"리액트":        "React",
"뷰":            "Vue.js",
"마이에스큐엘":  "MySQL",
"포스트그레스":  "PostgreSQL"
```

**변경 2 — 역방향 alias 매핑 + 확장 keyword_hit** (`pipeline.py`)

모듈 로드 시 `_REVERSE_ALIASES: dict[str, set[str]]`를 1회 생성.
`extract_required_skills`에서 기존 `keyword_hit` 체크를 아래 헬퍼로 교체.

```python
# 모듈 초기화 시 (SKILL_ALIASES 로드 후)
_REVERSE_ALIASES: dict[str, set[str]] = {}
for _alias, _norm in SKILL_ALIASES.items():
    _REVERSE_ALIASES.setdefault(_norm, set()).add(_alias)

def _keyword_hit_any(skill: str, sentence: str) -> bool:
    """정규화된 스킬명 + 모든 alias(한국어 포함)가 sentence에 등장하는지 확인."""
    sl = sentence.lower()
    if skill.lower() in sl:
        return True
    for alias in _REVERSE_ALIASES.get(skill, set()):
        if alias.lower() in sl:
            return True
    return False
```

`extract_required_skills` 내부 `keyword_hit` 판단을 `_keyword_hit_any(skill, sentence)` 호출로 교체.

**변경 3 — jd_extract 임계값 0.28 → 0.62** (`analyzer_rules.json`)

```json
"jd_extract": 0.62
```

의미: semantic similarity만으로 스킬을 추출하려면 62% 이상 유사도 필요.
키워드가 직접 등장하는 경우는 임계값 무관 포함 (기존 동일).

### 예상 결과

샘플 JD `"Spring Boot REST API, MySQL, Docker, AWS, CI/CD, Kubernetes, Kafka 우대"`:

| 스킬 | 이전 | 이후 | 이유 |
|------|------|------|------|
| Spring Boot | ✅ | ✅ | keyword |
| REST API | ✅ | ✅ | keyword |
| MySQL | ✅ | ✅ | keyword |
| Docker | ✅ | ✅ | keyword |
| AWS | ✅ | ✅ | keyword |
| CI/CD | ✅ | ✅ | keyword |
| Kubernetes | ✅ | ✅ | keyword |
| Kafka | ✅ | ✅ | keyword |
| Java | ✅ | ❌ | sim ~0.40, 임계값 미달 |
| OpenAPI | ✅ | ❌ | sim ~0.38, 임계값 미달 |
| PostgreSQL | ✅ | ❌ | sim ~0.29, 임계값 미달 |
| Kotlin | ✅ | ❌ | sim ~0.35, 임계값 미달 |
| Node.js | ✅ | ❌ | sim ~0.31, 임계값 미달 |
| JUnit | ✅ | ❌ | sim ~0.28, 임계값 미달 |
| Git | ✅ | ❌ | sim ~0.30, 임계값 미달 |

### 테스트 갱신 범위

`backend/tests/test_c_part_pipeline.py`:
- "JD에 없는 스킬은 required_skills에 포함되지 않는다" 어서션 추가
- Korean alias 매칭 케이스 추가

---

## 2. PDF OCR 파이프라인

### 문제

현재 `text_extractor.py`는 text-layer PDF만 처리. 스캔 이미지 PDF는
텍스트가 빈 문자열로 반환되고 사용자는 에러 메시지만 받는다.

### 설계: 2-단계 fallback

```
PDF 업로드
  │
  ├─ Step 1: pdfplumber — text-layer 추출
  │   └─ 페이지당 평균 50자 이상? → ✅ 완료 (extractor="pdfplumber")
  │
  └─ Step 2 (텍스트 빈약): pytesseract OCR
      ├─ 사용 가능? → OCR 실행 → ✅ (extractor="tesseract-ocr", warning 추가)
      └─ 미설치?   → ⚠️  명확한 안내 메시지 반환
```

**warning 메시지** (OCR 경로 사용 시):
```
"스캔 PDF를 OCR로 처리했습니다. 텍스트 인식 정확도가 낮을 수 있으니 미리보기에서 확인 후 수정하세요."
```

**의존성** (`requirements.txt` 추가):
```
pdfplumber>=0.11
pdf2image>=1.17
pytesseract>=0.3.10
```

`pytesseract`/`pdf2image`는 `ImportError` 시 graceful skip — 서버 기동 불필요.  
시스템 패키지 (`brew install tesseract poppler`) 없이도 서버는 정상 동작,
OCR path만 비활성화된다.

**변경 함수**: `extract_pdf_text()` 내부에 2-단계 로직 추가.
기존 PyPDF2 path는 레거시 fallback으로 유지 (하위 호환).

### 테스트

`backend/tests/test_text_extractor.py`:
- OCR path는 `pytesseract` mock으로 단위 테스트 (실제 tesseract 불필요)
- pdfplumber path: 기존 TXT-embedded PDF 픽스처 재사용

---

## 3. 입력 UX 기본값 변경

### 변경 사항

| 패널 | 현재 | 변경 후 |
|------|------|---------|
| JD 입력 탭 목록 | text · url · file(PDF/TXT) 3개 | **text · url 2개만** |
| JD default 탭 | text | **url** |
| 지원자 자료 탭 목록 | text · file(PDF/TXT) 2개 유지 | 유지 (변경 없음) |
| 지원자 자료 default 탭 | text | **file (PDF/TXT)** |

**의도**: 대표 시나리오 → `잡코리아 URL 붙여넣기` + `자소서 PDF 업로드` → `분석 시작`.

### 상세

**JD URL placeholder 개선** (`JobPostingInputPanel.tsx`):
```
https://www.jobkorea.co.kr/Recruit/GI_Read/...
잡코리아, 사람인, 원티드 등 채용공고 URL을 붙여넣으세요
```

**파일 탭 제거 이유**: JD는 공고 URL 또는 텍스트 복붙으로 충분.
PDF 채용공고를 직접 업로드하는 케이스는 드물며, URL 탭이 더 직관적.
지원자 자료(자소서)는 PDF 형태가 일반적이므로 file을 default로 유지.

### E2E 영향 분석

- `JobInputMode` 타입에서 `"file"` 제거 (`"text" | "url"` 로 좁힘)
- E2E test 1, 2: `jobPanel.locator("textarea")` — textarea는 URL 탭에서도 유지되므로 텍스트 fill 가능 ✅
- E2E test 2, 3: `jobPanel.getByRole("button", { name: "PDF/TXT" })` — JD 파일 탭이 제거되므로 **이 클릭이 작동 안 함** → E2E spec 갱신 필요
  - 해결: test 2, 3에서 JD 파일 업로드 부분을 **텍스트 직접 입력**으로 대체 (URL fetch는 네트워크 필요해 E2E 불안정)

---

## 4. 문서 동기화

탐색 대상: `docs/` 하위 전체 `.md` 파일.

교체 규칙:
```
"BAAI/bge-m3"  →  삭제 또는 "jhgan/ko-sroberta-multitask (로컬 fallback)"
fallback 설명  →  "text-embedding-3-small → jhgan/ko-sroberta-multitask → TF-IDF"
```

---

## 검증 계획

```bash
# 1. C-파트 단위 테스트
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_c_part_pipeline.py

# 2. 전체 백엔드 테스트
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests

# 3. 프론트엔드 빌드 (TypeScript)
npm --prefix frontend run build

# 4. E2E (갱신된 spec 기준 3 passed)
npm --prefix frontend run e2e
```

---

## 미적용 항목 (이번 범위 외)

- 스캔 PDF OCR 정확도 벤치마크 (시연 환경에서 tesseract 미설치 가능성)
- C-파트 성능 최적화 (임베딩 배치 처리)
- 발표 PPT 자동화 (D역할 범위 외)
