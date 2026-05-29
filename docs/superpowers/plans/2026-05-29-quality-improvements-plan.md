# Quality Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** C-파트 required_skills 과다 추출 수정, PDF OCR 추가, JD 입력 UX 간소화(text+url 2탭, 지원자 파일 기본), 문서 동기화.

**Architecture:** 백엔드 3개 파일(pipeline.py, analyzer_rules.json, skill_taxonomy.json, text_extractor.py, requirements.txt) + 프론트엔드 3개 파일(types.ts, JobPostingInputPanel.tsx, page.tsx) + E2E spec. 각 Task는 독립적으로 빌드+테스트 통과.

**Tech Stack:** Python 3.13, FastAPI, Ko-Sentence-RoBERTa, pdf2image, pytesseract, Next.js 16, React 19, Playwright

---

## 파일 구조

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `backend/app/services/c_part/analyzer_rules.json` | 수정 | `jd_extract` 0.28 → 0.65 (실측: max false-positive=0.594) |
| `backend/app/services/c_part/skill_taxonomy.json` | 수정 | Korean aliases 13개 추가 ("스프링" 단독 제외) |
| `backend/app/services/c_part/pipeline.py` | 수정 | `_REVERSE_ALIASES`, `_keyword_hit_any()`, 3개 라인 교체 |
| `backend/tests/test_c_part_pipeline.py` | 수정 | 과다 추출 테스트 2개 추가 |
| `backend/app/services/text_extractor.py` | 수정 | `_extract_pdf_with_ocr()` 추가, `extract_pdf_bytes()` 갱신 |
| `backend/requirements.txt` | 수정 | pdf2image, pytesseract 추가 (pdfplumber 미사용이므로 제외) |
| `backend/tests/test_text_extractor.py` | 수정 | OCR mock 테스트 2개 추가 |
| `frontend/lib/types.ts` | 수정 | `JobInputMode` 타입 좁힘 |
| `frontend/components/JobPostingInputPanel.tsx` | 수정 | file 탭 제거, `onFileChange` prop 제거, URL placeholder 개선 |
| `frontend/app/page.tsx` | 수정 | JD default→url, candidate default→file, JD 파일 관련 state/handler 제거 |
| `frontend/e2e/product-flow.spec.ts` | 수정 | test 2 JD파트 → 텍스트 입력, test 3 리퍼포즈 |
| `docs/final_rag_architecture.md` | 수정 | BAAI/bge-m3 → jhgan/ko-sroberta-multitask |
| `docs/final_end_to_end_flow_design.md` | 수정 | BAAI/bge-m3 → jhgan/ko-sroberta-multitask |

---

## Task 1: analyzer_rules.json — jd_extract 임계값 상향

**Files:**
- Modify: `backend/app/services/c_part/analyzer_rules.json`

- [ ] **Step 1: 현재 값 확인 후 변경**

  `analyzer_rules.json`의 `thresholds.jd_extract` 값을 `0.28`에서 `0.65`로 변경.
  (실측 근거: 최대 false-positive인 OpenAPI sim=0.594. margin=0.056 확보.)

  ```json
  "thresholds": {
    "skill_match": 0.45,
    "jd_extract": 0.65,
    "candidate_anchor": 0.3,
    "owned_skill": 0.35,
    "experience_verb_penalty": 0.6
  }
  ```

- [ ] **Step 2: JSON 문법 검증**

  ```bash
  python3 -c "import json; json.load(open('backend/app/services/c_part/analyzer_rules.json')); print('OK')"
  ```

  Expected: `OK`

- [ ] **Step 3: 커밋**

  ```bash
  git add backend/app/services/c_part/analyzer_rules.json
  git commit -m "config: raise jd_extract threshold 0.28→0.62 to reduce over-extraction"
  ```

---

## Task 2: skill_taxonomy.json — Korean aliases 추가

**Files:**
- Modify: `backend/app/services/c_part/skill_taxonomy.json`

- [ ] **Step 1: aliases 객체에 한국어 표기 14개 추가**

  `aliases` 객체에 아래 항목들을 추가한다. 기존 항목은 수정하지 않는다.

  ```json
  "스프링 부트": "Spring Boot",
  "자바": "Java",
  "도커": "Docker",
  "쿠버네티스": "Kubernetes",
  "카프카": "Kafka",
  "레디스": "Redis",
  "깃": "Git",
  "파이썬": "Python",
  "텐서플로우": "TensorFlow",
  "파이토치": "PyTorch",
  "리액트": "React",
  "마이에스큐엘": "MySQL",
  "포스트그레스": "PostgreSQL"
  ```

- [ ] **Step 2: JSON 문법 검증**

  ```bash
  python3 -c "
  import json
  d = json.load(open('backend/app/services/c_part/skill_taxonomy.json'))
  aliases = d['aliases']
  assert aliases.get('스프링 부트') == 'Spring Boot', '스프링 부트 alias 누락'
  assert aliases.get('도커') == 'Docker', '도커 alias 누락'
  print('aliases OK:', len(aliases), '개')
  "
  ```

  Expected: `aliases OK: N개` (기존 개수 + 14)

- [ ] **Step 3: 커밋**

  ```bash
  git add backend/app/services/c_part/skill_taxonomy.json
  git commit -m "config: add Korean skill name aliases (스프링 부트, 도커 etc)"
  ```

---

## Task 3: pipeline.py — _REVERSE_ALIASES + _keyword_hit_any + 3개 사용처 교체

**Files:**
- Modify: `backend/app/services/c_part/pipeline.py`

- [ ] **Step 1: _REVERSE_ALIASES 빌드 + _keyword_hit_any 추가**

  파일 내 `SKILL_ALIASES = _TAXONOMY["aliases"]` 라인 바로 아래에 다음을 추가한다.

  ```python
  import re as _re  # (파일 상단에 이미 import re 있으므로 이 줄은 추가하지 않음)

  # 역방향 alias 맵: 정규화된 스킬명 → {alias1, alias2, ...}  (모듈 로드 시 1회 생성)
  _REVERSE_ALIASES: dict[str, set[str]] = {}
  for _alias, _norm in SKILL_ALIASES.items():
      _REVERSE_ALIASES.setdefault(_norm, set()).add(_alias)


  def _keyword_hit_any(skill: str, sentence: str) -> bool:
      """word-boundary regex로 스킬명 + alias가 sentence에 등장하는지 확인.

      substring 'in' 대신 (?<!\\w)term(?!\\w) 사용:
        - "Java" in "JavaScript"  → False  (substring 방식은 True)
        - "Git"  in "GitHub"      → False  (substring 방식은 True)
      """
      def _hit(term: str, text: str) -> bool:
          pattern = rf'(?<!\w){re.escape(term)}(?!\w)'
          return bool(re.search(pattern, text, re.IGNORECASE))

      if _hit(skill, sentence):
          return True
      for alias in _REVERSE_ALIASES.get(skill, set()):
          if _hit(alias, sentence):
              return True
      return False
  ```

- [ ] **Step 2: extract_required_skills — keyword_hit 교체 (line 275)**

  `extract_required_skills` 함수 내 아래 라인을 찾아서:
  ```python
  keyword_hit = skill.lower() in sentence.lower()
  ```
  다음으로 교체한다:
  ```python
  keyword_hit = _keyword_hit_any(skill, sentence)
  ```

- [ ] **Step 3: extract_owned_skills — keyword_hit 교체 (line 330)**

  `extract_owned_skills` 함수 내 동일한 패턴을 교체한다:
  ```python
  # Before:
  keyword_hit = skill.lower() in sentence.lower()
  # After:
  keyword_hit = _keyword_hit_any(skill, sentence)
  ```

- [ ] **Step 4: gap 분석 루프 — keyword_hit 교체 (line 576)**

  `run_c_part_analysis` 내 gap 계산 루프에서 동일 교체:
  ```python
  # Before:
  keyword_hit = skill.lower() in sentence.lower()
  # After:
  keyword_hit = _keyword_hit_any(skill, sentence)
  ```

- [ ] **Step 5: 검증 — word-boundary + Korean alias 확인**

  ```bash
  PYTHONPATH=backend .venv/bin/python -c "
  from app.services.c_part.pipeline import _keyword_hit_any, _REVERSE_ALIASES

  # 한국어 alias 매칭
  assert _keyword_hit_any('Spring Boot', '스프링 부트 개발 경험'), 'Korean alias fail'
  assert _keyword_hit_any('Docker', '도커 컨테이너 배포'), 'Korean alias fail'
  assert _keyword_hit_any('Spring Boot', 'Spring Boot 기반 API 개발'), 'English keyword fail'

  # word-boundary: substring 방식에서 false positive였던 케이스
  assert not _keyword_hit_any('Java', 'JavaScript TypeScript 개발'), 'Java/JavaScript boundary fail'
  assert not _keyword_hit_any('Git', 'GitHub Actions CI/CD 파이프라인'), 'Git/GitHub boundary fail'

  # 정상 매칭
  assert _keyword_hit_any('Java', 'Java Spring Boot 개발'), 'Java exact match fail'
  assert _keyword_hit_any('Git', 'Git 버전 관리 경험'), 'Git exact match fail'

  print('모든 _keyword_hit_any 검증 통과')
  print('Spring Boot aliases:', sorted(_REVERSE_ALIASES.get('Spring Boot', set())))
  "
  ```

  Expected:
  ```
  모든 _keyword_hit_any 검증 통과
  Spring Boot aliases: ['SpringBoot', 'spring boot', 'springboot', '스프링 부트']
  ```

- [ ] **Step 6: 커밋**

  ```bash
  git add backend/app/services/c_part/pipeline.py
  git commit -m "feat(c-part): add _REVERSE_ALIASES and _keyword_hit_any for Korean JD support"
  ```

---

## Task 4: C-파트 테스트 추가

**Files:**
- Modify: `backend/tests/test_c_part_pipeline.py`

- [ ] **Step 1: 테스트 클래스에 2개 메서드 추가**

  기존 테스트 클래스 내부에 아래 세 메서드를 추가한다.
  (경고: 처음 두 테스트는 실제 모델 추론이 필요해 각 ~30초 소요됨)

  ```python
  def test_extract_required_skills_no_overextraction(self) -> None:
      """JD에 명시되지 않은 스킬이 required_skills에 포함되지 않아야 한다."""
      from app.services.c_part.pipeline import (
          extract_required_skills,
          get_embedding,
          split_sentences,
      )

      jd_text = (
          "Spring Boot 기반 REST API 개발 경험 필수.\n"
          "MySQL 데이터 모델링 및 쿼리 최적화.\n"
          "Docker 컨테이너 배포 경험 필요.\n"
          "AWS 클라우드 운영. CI/CD 파이프라인 구축."
      )
      jd_sentences = split_sentences(jd_text)
      jd_vectors = [get_embedding(s) for s in jd_sentences]

      result = extract_required_skills("backend", jd_sentences, jd_vectors)
      skill_names = [r["skill"] for r in result]

      # JD에 명시된 기술은 포함
      assert "Spring Boot" in skill_names, f"Spring Boot 누락: {skill_names}"
      assert "REST API" in skill_names, f"REST API 누락: {skill_names}"
      assert "MySQL" in skill_names, f"MySQL 누락: {skill_names}"
      assert "Docker" in skill_names, f"Docker 누락: {skill_names}"

      # JD에 없는 기술은 포함 불가
      assert "Java" not in skill_names, f"Java 과다 추출: {skill_names}"
      assert "Kotlin" not in skill_names, f"Kotlin 과다 추출: {skill_names}"
      assert "OpenAPI" not in skill_names, f"OpenAPI 과다 추출: {skill_names}"
      assert "PostgreSQL" not in skill_names, f"PostgreSQL 과다 추출: {skill_names}"
      assert "Node.js" not in skill_names, f"Node.js 과다 추출: {skill_names}"
      assert "JUnit" not in skill_names, f"JUnit 과다 추출: {skill_names}"

  def test_extract_required_skills_korean_aliases(self) -> None:
      """한국어 기술명 JD에서 정규화된 영문명으로 추출되어야 한다."""
      from app.services.c_part.pipeline import (
          extract_required_skills,
          get_embedding,
          split_sentences,
      )

      jd_text = (
          "스프링 부트 기반 백엔드 개발 경험 3년 이상 필수.\n"
          "도커를 활용한 컨테이너 배포 경험.\n"
          "쿠버네티스 운영 경험 우대."
      )
      jd_sentences = split_sentences(jd_text)
      jd_vectors = [get_embedding(s) for s in jd_sentences]

      result = extract_required_skills("backend", jd_sentences, jd_vectors)
      skill_names = [r["skill"] for r in result]

      assert "Spring Boot" in skill_names, (
          f"'스프링 부트' → 'Spring Boot' alias 매칭 실패: {skill_names}"
      )
      assert "Docker" in skill_names, (
          f"'도커' → 'Docker' alias 매칭 실패: {skill_names}"
      )
      assert "Kubernetes" in skill_names, (
          f"'쿠버네티스' → 'Kubernetes' alias 매칭 실패: {skill_names}"
      )

  def test_keyword_hit_word_boundary_no_false_positive(self) -> None:
      """Java/Git 등이 JavaScript/GitHub에서 잘못 추출되지 않아야 한다."""
      from app.services.c_part.pipeline import _keyword_hit_any

      # word-boundary: 이전 substring 방식의 false positive 케이스
      assert not _keyword_hit_any("Java", "JavaScript TypeScript 개발 경험"), \
          "Java must not match inside JavaScript"
      assert not _keyword_hit_any("Git", "GitHub Actions, GitLab CI/CD 사용"), \
          "Git must not match inside GitHub/GitLab"

      # 정상 매칭: 단어 경계에서 정확히 있는 경우
      assert _keyword_hit_any("Java", "Java와 Spring Boot 기반 REST API 개발"), \
          "Java exact match must pass"
      assert _keyword_hit_any("Git", "Git, SVN 버전 관리 경험 보유"), \
          "Git exact match must pass"
  ```

- [ ] **Step 2: 테스트 실행 (느림 — ~2분 예상)**

  ```bash
  cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp" && \
  PYTHONPATH=backend .venv/bin/python -m unittest \
    backend.tests.test_c_part_pipeline -v 2>&1 | tail -15
  ```

  Expected: 기존 3개 + 신규 3개 모두 `OK`

- [ ] **Step 3: 전체 백엔드 테스트**

  ```bash
  PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | grep -E "^(Ran|OK|FAIL|ERROR)"
  ```

  Expected: `Ran 44 tests` / `OK`

- [ ] **Step 4: 커밋**

  ```bash
  git add backend/tests/test_c_part_pipeline.py
  git commit -m "test(c-part): add over-extraction, Korean alias, and word-boundary tests"
  ```

---

## Task 5: text_extractor.py — OCR 파이프라인 추가

**Files:**
- Modify: `backend/app/services/text_extractor.py`

- [ ] **Step 1: _extract_pdf_with_ocr 함수 추가**

  파일 끝의 `_VisibleTextParser` 클래스 위에 아래 함수를 추가한다.

  ```python
  def _extract_pdf_with_ocr(content: bytes) -> tuple[str, list[str]]:
      """pdf2image + pytesseract OCR. 패키지 미설치 시 빈 문자열 반환 (graceful skip)."""
      try:
          from pdf2image import convert_from_bytes
          import pytesseract
      except ImportError:
          return "", []

      try:
          images = convert_from_bytes(content, dpi=200)
          parts: list[str] = []
          for img in images:
              text = pytesseract.image_to_string(img, lang="kor+eng")
              if text.strip():
                  parts.append(text.strip())
          result = clean_text("\n".join(parts))
          warnings = (
              [
                  "스캔 PDF를 OCR로 처리했습니다. "
                  "텍스트 인식 정확도가 낮을 수 있으니 미리보기에서 확인 후 수정하세요."
              ]
              if result
              else []
          )
          return result, warnings
      except Exception:
          return "", []
  ```

- [ ] **Step 2: extract_pdf_bytes 갱신**

  기존 `extract_pdf_bytes` 함수를 아래로 **완전 교체** (기존 함수 전체 삭제 후 교체):

  ```python
  def extract_pdf_bytes(content: bytes) -> TextExtractionResult:
      warnings: list[str] = []
      extractor = "pdf_text_extractor"

      # Stage 1: PyPDF2
      try:
          text, pypdf_warnings = _extract_pdf_with_pypdf(content)
          warnings.extend(pypdf_warnings)
      except TextExtractionError:
          text = ""
          warnings.append("PyPDF2 추출 실패 후 pdftotext fallback을 사용했습니다.")

      # Stage 2: pdftotext (시스템 커맨드)
      if not text:
          text = _extract_pdf_with_pdftotext(content)
          if text and not any("pdftotext" in w for w in warnings):
              warnings.append("PyPDF2 결과가 비어 있어 pdftotext fallback을 사용했습니다.")

      # Stage 3: OCR (스캔 PDF)
      if not text:
          text, ocr_warnings = _extract_pdf_with_ocr(content)
          if text:
              extractor = "tesseract-ocr"
              warnings.extend(ocr_warnings)

      if not text:
          raise TextExtractionError(
              "PDF에서 텍스트를 추출하지 못했습니다. "
              "스캔 PDF라면 직접 붙여넣어 주세요."
          )
      return TextExtractionResult(
          text=text,
          source_type="pdf",
          extractor=extractor,
          warnings=warnings,
      )
  ```

- [ ] **Step 3: 구문 검증**

  ```bash
  PYTHONPATH=backend .venv/bin/python -c "
  from app.services.text_extractor import _extract_pdf_with_ocr, extract_pdf_bytes
  print('import OK')
  # OCR 미설치 환경에서도 빈 문자열 반환해야 함
  text, warnings = _extract_pdf_with_ocr(b'fake-pdf-bytes')
  print('OCR graceful skip OK:', repr(text), warnings)
  "
  ```

  Expected: `import OK` + `OCR graceful skip OK: '' []` (또는 tesseract 있으면 다른 결과)

- [ ] **Step 4: 커밋**

  ```bash
  git add backend/app/services/text_extractor.py
  git commit -m "feat: add OCR pipeline (pdf2image + pytesseract) as 3rd PDF extraction stage"
  ```

---

## Task 6: requirements.txt + OCR 테스트

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/tests/test_text_extractor.py`

- [ ] **Step 1: requirements.txt에 OCR 패키지 추가**

  파일 끝에 아래 2줄 추가 (pdfplumber는 코드에서 사용하지 않으므로 제외):

  ```
  pdf2image>=1.17
  pytesseract>=0.3.10
  ```

- [ ] **Step 2: OCR 테스트 2개 추가** (`test_text_extractor.py` 기존 클래스에 추가)

  ```python
  def test_extract_pdf_bytes_falls_back_to_ocr_when_pypdf_returns_empty(self) -> None:
      """PyPDF2와 pdftotext가 모두 빈 결과를 내면 OCR을 시도해야 한다."""
      from unittest.mock import patch, MagicMock
      from app.services.text_extractor import extract_pdf_bytes

      # PyPDF2 → 빈 문자열, pdftotext → 빈 문자열, OCR → "추출된 텍스트"
      with (
          patch(
              "app.services.text_extractor._extract_pdf_with_pypdf",
              return_value=("", []),
          ),
          patch(
              "app.services.text_extractor._extract_pdf_with_pdftotext",
              return_value="",
          ),
          patch(
              "app.services.text_extractor._extract_pdf_with_ocr",
              return_value=("추출된 텍스트", ["스캔 PDF를 OCR로 처리했습니다."]),
          ),
      ):
          result = extract_pdf_bytes(b"fake-pdf")

      assert result.text == "추출된 텍스트"
      assert result.extractor == "tesseract-ocr"
      assert any("OCR" in w for w in result.warnings)

  def test_extract_pdf_with_ocr_returns_empty_on_import_error(self) -> None:
      """pdf2image 미설치 시 예외 없이 빈 문자열을 반환해야 한다."""
      import sys
      from unittest.mock import patch
      from app.services.text_extractor import _extract_pdf_with_ocr

      # sys.modules에 None을 넣으면 해당 모듈 import 시 ImportError가 발생함
      with patch.dict(sys.modules, {"pdf2image": None}):
          text, warnings = _extract_pdf_with_ocr(b"fake-pdf")

      assert text == ""
      assert warnings == []
  ```

- [ ] **Step 3: 전체 백엔드 테스트 실행**

  ```bash
  cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp" && \
  PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | grep -E "^(Ran|OK|FAIL|ERROR)"
  ```

  Expected: `Ran 46 tests` / `OK`

- [ ] **Step 4: 커밋**

  ```bash
  git add backend/requirements.txt backend/tests/test_text_extractor.py
  git commit -m "test: add OCR mock tests; add pdfplumber/pdf2image/pytesseract to requirements"
  ```

---

## Task 7: UX — JD 입력 2탭 + 기본값 변경

**Files:**
- Modify: `frontend/lib/types.ts`
- Modify: `frontend/components/JobPostingInputPanel.tsx`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: types.ts — JobInputMode 좁히기**

  `types.ts` 91번째 줄 근처:
  ```typescript
  // Before:
  export type JobInputMode = "text" | "url" | "file";
  // After:
  export type JobInputMode = "text" | "url";
  ```

- [ ] **Step 2: JobPostingInputPanel.tsx — file 탭 제거 + onFileChange prop 제거**

  **Props에서 `onFileChange` 제거:**
  ```typescript
  // Before:
  type Props = {
    value: string;
    onChange: (value: string) => void;
    sourceMode: JobInputMode;
    onSourceModeChange: (value: JobInputMode) => void;
    url: string;
    onUrlChange: (value: string) => void;
    onExtractUrl: () => void;
    onFileChange: (file: File) => void;
    isExtracting: boolean;
    sourceName?: string;
    extractor?: string;
    warnings: string[];
    error: string | null;
  };
  // After (onFileChange 제거):
  type Props = {
    value: string;
    onChange: (value: string) => void;
    sourceMode: JobInputMode;
    onSourceModeChange: (value: JobInputMode) => void;
    url: string;
    onUrlChange: (value: string) => void;
    onExtractUrl: () => void;
    isExtracting: boolean;
    sourceName?: string;
    extractor?: string;
    warnings: string[];
    error: string | null;
  };
  ```

  **sourceModes 배열에서 file 제거:**
  ```typescript
  // Before:
  const sourceModes: Array<{ value: JobInputMode; label: string }> = [
    { value: "text", label: "텍스트" },
    { value: "url", label: "URL" },
    { value: "file", label: "PDF/TXT" },
  ];
  // After:
  const sourceModes: Array<{ value: JobInputMode; label: string }> = [
    { value: "text", label: "텍스트" },
    { value: "url", label: "URL" },
  ];
  ```

  **함수 시그니처에서 onFileChange 제거:**
  ```typescript
  // Before:
  export function JobPostingInputPanel({
    value, onChange, sourceMode, onSourceModeChange,
    url, onUrlChange, onExtractUrl, onFileChange,
    isExtracting, sourceName, extractor, warnings, error,
  }: Props) {
  // After:
  export function JobPostingInputPanel({
    value, onChange, sourceMode, onSourceModeChange,
    url, onUrlChange, onExtractUrl,
    isExtracting, sourceName, extractor, warnings, error,
  }: Props) {
  ```

  **file 업로드 JSX 블록 완전 제거:**
  ```typescript
  // 아래 블록 전체 삭제:
  {sourceMode === "file" ? (
    <label className="file-drop">
      <span>채용공고 PDF/TXT 업로드</span>
      <input
        type="file"
        accept=".pdf,.txt,application/pdf,text/plain"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFileChange(file);
          event.currentTarget.value = "";
        }}
      />
    </label>
  ) : null}
  ```

  **URL placeholder 개선** (url input의 placeholder 속성):
  ```typescript
  // Before:
  placeholder="https://example.com/job"
  // After:
  placeholder="https://www.jobkorea.co.kr/Recruit/GI_Read/..."
  ```

  **URL 탭 아래 힌트 텍스트 추가** (url input 아래):
  ```typescript
  {sourceMode === "url" ? (
    <div className="source-action">
      <input ... placeholder="https://www.jobkorea.co.kr/Recruit/GI_Read/..." />
      <button ...>...</button>
    </div>
  ) : null}
  // 위 블록 뒤에 추가:
  {sourceMode === "url" ? (
    <p className="field-help">잡코리아, 사람인, 원티드 등 채용공고 URL을 붙여넣으세요.</p>
  ) : null}
  ```

- [ ] **Step 3: page.tsx — 기본값 변경 + JD 파일 관련 코드 정리**

  **JD source mode 기본값 변경:**
  ```typescript
  // Before:
  const [jobSourceMode, setJobSourceMode] = useState<JobInputMode>("text");
  // After:
  const [jobSourceMode, setJobSourceMode] = useState<JobInputMode>("url");
  ```

  **candidate material 기본 sourceMode 변경** (`createCandidate` 함수):
  ```typescript
  // Before:
  const createCandidate = (id: string): CandidateMaterialDraft => ({
    id,
    label: "자소서",
    sourceMode: "text",
    ...
  });
  // After:
  const createCandidate = (id: string): CandidateMaterialDraft => ({
    id,
    label: "자소서",
    sourceMode: "file",
    ...
  });
  ```

  **JD 파일 관련 state + handler 제거** (다음 4개 항목 삭제):
  ```typescript
  // 삭제할 state:
  const [isJobExtracting, setIsJobExtracting] = useState(false);

  // 삭제할 handler:
  async function handleExtractJobFile(file: File) { ... }
  ```

  **SetupPage 컴포넌트에서 제거된 props 정리:**
  - `SetupPage` props 타입에서 `isJobExtracting`, `setIsJobExtracting`, `onExtractJobFile` 제거
  - `SetupPage` 함수 시그니처에서 동일 제거
  **page.tsx의 SetupPage props 타입에서 onExtractJobFile 제거:**
  ```typescript
  // SetupPage 컴포넌트 props 타입에서 아래 항목 삭제:
  onExtractJobFile: (f: File) => void;

  // SetupPage 함수 파라미터에서도 삭제:
  // Before:
  function SetupPage({
    ...
    onExtractJobFile,
    ...
  }: { ... onExtractJobFile: (f: File) => void; ... }) {
  // After: onExtractJobFile 제거

  // SetupPage JSX 내 JobPostingInputPanel 호출에서 제거:
  // Before:
  <JobPostingInputPanel
    ...
    onFileChange={onExtractJobFile}
    isExtracting={isJobExtracting}
    ...
  />
  // After: onFileChange 줄만 삭제, isExtracting={isJobExtracting} 유지
  ```

  **Home 컴포넌트에서 handleExtractJobFile 함수 전체 삭제:**
  ```typescript
  // 삭제할 함수 전체:
  async function handleExtractJobFile(file: File) {
    setJobExtractionError(null);
    setIsJobExtracting(true);
    try {
      const extracted = await extractJobPostingFromFile(file);
      ...
    } finally {
      setIsJobExtracting(false);
    }
  }
  ```

  **Home 컴포넌트의 SetupPage JSX 호출에서 prop 제거:**
  ```typescript
  // Before:
  <SetupPage
    ...
    onExtractJobFile={handleExtractJobFile}
    ...
  />
  // After: onExtractJobFile 줄 삭제
  ```

  요약: `handleExtractJobFile` 함수, `onExtractJobFile` prop 선언/전달 3곳만 제거. `isJobExtracting` state와 `handleExtractJobUrl` handler는 건드리지 않는다.

- [ ] **Step 4: TypeScript 빌드 확인**

  ```bash
  npm --prefix frontend run build 2>&1 | tail -10
  ```

  Expected: `✓ Compiled successfully` (no TypeScript errors)

- [ ] **Step 5: 커밋**

  ```bash
  git add frontend/lib/types.ts frontend/components/JobPostingInputPanel.tsx frontend/app/page.tsx
  git commit -m "feat(ux): JD input text+url only, candidate default file, URL hint for jobkorea"
  ```

---

## Task 8: E2E 테스트 갱신

**Files:**
- Modify: `frontend/e2e/product-flow.spec.ts`

- [ ] **Step 1: test 2 JD 파트 — 파일 업로드 → 텍스트 입력으로 교체**

  Test 2 이름 변경 (선택):
  ```typescript
  // Before:
  test("사용자가 TXT 파일을 업로드하면 추출 미리보기 후 분析까지 진행된다", ...
  // After:
  test("사용자가 JD 텍스트 + 지원자 TXT 파일 업로드로 분析할 수 있다", ...
  ```

  Test 2 본문에서 JD 파일 업로드 부분 교체:
  ```typescript
  // Before (삭제):
  const jobPanel = page.locator('section[aria-label="지원할 채용공고"]');
  await jobPanel.getByRole("button", { name: "PDF/TXT" }).click();
  await jobPanel.locator('input[type="file"]').setInputFiles(jobFile);
  await expect(jobPanel.locator("textarea")).toContainText("Docker 컨테이너 기반 배포");

  // After (교체):
  const jobPanel = page.locator('section[aria-label="지원할 채용공고"]');
  await jobPanel.getByRole("button", { name: "텍스트" }).click();
  await jobPanel.locator("textarea").fill(jobPostingText);
  await expect(jobPanel.locator("textarea")).toContainText("Docker 컨테이너 기반 배포");
  ```

  Test 2 candidate 파트 — `PDF/TXT` 버튼 클릭 제거 (file이 이미 기본값):
  ```typescript
  // Before:
  await candidatePanel.getByRole("button", { name: "PDF/TXT" }).click();
  await candidatePanel.locator('input[type="file"]').setInputFiles(candidateFile);
  // After:
  // PDF/TXT is now the default tab — no click needed
  await candidatePanel.locator('input[type="file"]').setInputFiles(candidateFile);
  ```

- [ ] **Step 2: test 3 리퍼포즈 — JD URL 탭 기본 동작 + 분析 검증**

  Test 3 전체를 아래로 교체 (cupsfilter 의존성 제거):
  ```typescript
  test("JD URL 탭이 기본으로 활성화되어 있고 텍스트 전환 후 분析이 완료된다", async ({ page }) => {
    await page.goto("/");

    const jobPanel = page.locator('section[aria-label="지원할 채용공고"]');
    // URL tab should be selected by default
    const urlBtn = jobPanel.getByRole("button", { name: "URL" });
    await expect(urlBtn).toHaveClass(/selected/);

    // Switch to text and fill
    await jobPanel.getByRole("button", { name: "텍스트" }).click();
    await jobPanel.locator("textarea").fill(jobPostingText);

    const candidatePanel = page.locator('section[aria-label="내 지원 자료"]');
    await candidatePanel.locator("textarea").fill(candidateText);

    await page.getByRole("button", { name: "분析 시작" }).click();

    await expect(page.locator(".score-board")).toBeVisible({ timeout: 180_000 });
    await expect(page.getByText("Curated RAG Resources")).toBeVisible();
  });
  ```

- [ ] **Step 3: E2E 실행**

  서버 2개가 실행 중이어야 함:
  ```bash
  tmux has-session -t nlp-backend-8010 && echo "backend up" || echo "BACKEND DOWN"
  tmux has-session -t nlp-frontend-3010 && echo "frontend up" || echo "FRONTEND DOWN"
  ```

  ```bash
  npm --prefix frontend run e2e 2>&1
  ```

  Expected: `3 passed`

- [ ] **Step 4: 커밋**

  ```bash
  git add frontend/e2e/product-flow.spec.ts
  git commit -m "test(e2e): update tests for JD 2-tab UX and candidate file default"
  ```

---

## Task 9: 문서 동기화

**Files:**
- Modify: `docs/final_rag_architecture.md`
- Modify: `docs/final_end_to_end_flow_design.md`

- [ ] **Step 1: final_rag_architecture.md 수정**

  Line 166:
  ```markdown
  # Before:
  API key가 없거나 OpenAI 임베딩 호출이 실패하면 무료 로컬 임베딩 모델인 `BAAI/bge-m3`로 fallback한다. `BAAI/bge-m3`는 한국어와 영어 기술명이 섞인 query를 의미 기반으로 검색할 수 있어 TF-IDF보다 추천 품질을 높일 가능성이 크다. 로컬 모델 로딩까지 실패한 경우에만 TF-IDF를 마지막 안전장치로 사용한다.
  # After:
  API key가 없거나 OpenAI 임베딩 호출이 실패하면 로컬 임베딩 모델인 `jhgan/ko-sroberta-multitask`로 fallback한다. 로컬 모델 로딩까지 실패한 경우에만 TF-IDF를 마지막 안전장치로 사용한다. (실제 fallback 체인: `text-embedding-3-small` → `jhgan/ko-sroberta-multitask` → TF-IDF)
  ```

  Line 279:
  ```markdown
  # Before:
  - OpenAI `text-embedding-3-small` 임베딩 검색과 `BAAI/bge-m3` 로컬 임베딩 fallback
  # After:
  - OpenAI `text-embedding-3-small` 임베딩 검색과 `jhgan/ko-sroberta-multitask` 로컬 임베딩 fallback
  ```

- [ ] **Step 2: final_end_to_end_flow_design.md 수정**

  Line 449 근처 `BAAI/bge-m3` → `jhgan/ko-sroberta-multitask` 교체.

- [ ] **Step 3: 잔존 레퍼런스 없는지 확인**

  ```bash
  grep -rn "BAAI/bge-m3" docs/ --include="*.md" | grep -v "specs/"
  ```

  Expected: 출력 없음 (스펙 문서 제외)

- [ ] **Step 4: 커밋**

  ```bash
  git add docs/final_rag_architecture.md docs/final_end_to_end_flow_design.md
  git commit -m "docs: replace BAAI/bge-m3 with jhgan/ko-sroberta-multitask (actual fallback)"
  ```

---

## 최종 검증

- [ ] **전체 백엔드 테스트**

  ```bash
  PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | grep -E "^(Ran|OK|FAIL|ERROR)"
  ```

  Expected: `Ran 46 tests` / `OK`

- [ ] **프론트엔드 빌드**

  ```bash
  npm --prefix frontend run build 2>&1 | tail -5
  ```

  Expected: `✓ Compiled successfully`

- [ ] **E2E 3종**

  ```bash
  npm --prefix frontend run e2e 2>&1
  ```

  Expected: `3 passed`
