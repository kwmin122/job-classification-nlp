# 분석 품질 근본 재설계 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 잡코리아 RSC skills 배열 직접 파싱 + coverage 단일 기준 재설계 + 로드맵/리포트/UI 개선으로 분석 품질 근본 향상.

**Architecture:** JD 추출은 RSC `__next_f` 페이로드에서 `skills`(HARD_SKILL)+`workFields` 직접 파싱 → relevance 필터 → coverage(0~100) 단일 지표로 owned(≥70)/partial(40-69)/missing(<40) 분류 → fit_score=coverage 평균 → 로드맵·리포트·UI 모두 coverage 단일 소스 사용. schema 변경(Task 0)이 모든 태스크의 전제.

**Tech Stack:** Python 3.13 + FastAPI + Ko-SRoBERTa(jhgan/ko-sroberta-multitask) + Next.js 14 + TypeScript + Playwright E2E

---

## 파일 맵

| 파일 | 변경 내용 |
|---|---|
| `backend/app/schemas.py` | `SkillGap/PartialSkill/MissingSkill`에 `coverage` 추가; `AnalyzeResponse`에 `jd_quality`, `structured_skills` 추가 |
| `backend/app/services/text_extractor.py` | `TextExtractionResult`에 `structured_skills`, `job_title` 추가; `_decode_jobkorea_rsc`, `_extract_jobkorea_skills`, `_extract_jobkorea_workfield` 신규 |
| `backend/app/services/c_part/skill_taxonomy.json` | aliases 확장(JAVA→Java, Restful API→REST API, Go/Golang 등); skills에 Go·NoSQL·LLMOps·AI Agent·RPA·LangChain 신규 추가 |
| `backend/app/services/c_part/pipeline.py` | coverage 계산 로직; `explicit_required_skills` 파라미터; `_filter_analyzable_skills`; `_compute_fit_score` 재설계 |
| `backend/app/main.py` | `/analyze` 핸들러 — structured_skills 있으면 explicit_required_skills 주입; classify_job 입력 보강 |
| `backend/app/services/roadmap_generator.py` | `distribute_weeks` 1-스킬 버그 수정; PHASES 도입 |
| `backend/app/services/report_generator.py` | evidence 원문 제거; coverage 기반 구조 ① 직무·적합도 ② 충족/보완/부족 카운트 ③ 최우선 보완 ④ 로드맵 요약 |
| `backend/app/data/learning_resources.csv` | LLMOps, AI Agent, LangChain, Go, NoSQL, RPA 등 신규 24+ 행 추가 |
| `backend/tools/measure_coverage_baseline.py` | 신규: "맨 스킬 단어 → 지원자 문장" sim 분포 측정 스크립트 |
| `backend/tests/fixtures/jobkorea_49244543.html` | AI마케팅 공고 fixture |
| `backend/tests/fixtures/jobkorea_43134476.html` | 백엔드 공고 fixture |
| `backend/tests/fixtures/jobkorea_48391099.html` | 백엔드 공고 fixture |
| `backend/tests/test_text_extractor.py` | RSC 파싱 테스트 추가 |
| `backend/tests/test_c_part_pipeline.py` | coverage 경계값 테스트; fit_score 재측정값 업데이트 |
| `frontend/lib/types.ts` | `AnalyzeResponse`에 `jd_quality`, `structured_skills`, skill 항목에 `coverage` 추가 |
| `frontend/app/page.tsx` | jd_quality 경고 배너; coverage% 카드; 추천자료 reason 표시 |

---

## Task 0: 스키마 확정 (backend + frontend 동기화)

**Files:**
- Modify: `backend/app/schemas.py`
- Modify: `frontend/lib/types.ts`

- [ ] **Step 0.1: schemas.py 변경 — SkillGap/PartialSkill/MissingSkill에 coverage 추가**

```python
# backend/app/schemas.py
class SkillGap(BaseModel):
    skill: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    evidence: str
    coverage: float = Field(ge=0, le=100, default=0.0)  # NEW


class PartialSkill(BaseModel):
    skill: str
    evidence: str
    evidence_strength: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    note: str = ""
    coverage: float = Field(ge=0, le=100, default=0.0)  # NEW


class MissingSkill(BaseModel):
    skill: str
    gap_score: float = Field(ge=0, le=100)
    gap_level: str
    importance: str
    evidence: str
    coverage: float = Field(ge=0, le=100, default=0.0)  # NEW
```

- [ ] **Step 0.2: schemas.py 변경 — AnalyzeResponse에 jd_quality, structured_skills 추가**

`AnalyzeResponse` 클래스에 다음 두 필드를 추가 (기존 필드 유지, 끝에 append):
```python
class AnalyzeResponse(BaseModel):
    # ... 기존 필드 모두 유지 ...
    jd_quality: Literal["ok", "weak"] = "ok"          # NEW: H영역
    structured_skills: list[str] = Field(default_factory=list)  # NEW: 공고 명시 전체 기술 (표시용)
```

- [ ] **Step 0.3: 스키마 변경 후 기존 테스트 확인 — 깨지면 기록만**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -10
```
예상: 현재 46 테스트 OK. 스키마에 default값 설정했으므로 깨지면 안 됨. 깨지는 케이스 있으면 아래 Task 5에서 수정 예정.

- [ ] **Step 0.4: frontend/lib/types.ts 동기화**

```typescript
// frontend/lib/types.ts — 변경 부분만 표시

export type SkillGap = {
  skill: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  evidence: string;
  coverage: number; // NEW
};

export type PartialSkill = {
  skill: string;
  evidence: string;
  evidence_strength: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  note: string;
  coverage: number; // NEW
};

export type MissingSkill = {
  skill: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  evidence: string;
  coverage: number; // NEW
};

// AnalyzeResponse 타입 — 아직 없으면 추가, 있으면 아래 필드 append
export type AnalyzeResponse = {
  predicted_job: string;
  job_label: string | null;
  job_probabilities: Record<string, number>;
  classifier_source: string;
  fit_score: number;
  roadmap_preferences: RoadmapPreferences;
  required_skills: RequiredSkill[];
  owned_skills: OwnedSkill[];
  partial_skills: PartialSkill[];
  missing_skills: MissingSkill[];
  recommended_resources: SkillRecommendation[];
  weekly_roadmap: WeeklyRoadmapItem[];
  report: string;
  scoring_formula: string;
  rag_scope_note: string;
  retrieval_mode: string;
  embedding_model: string;
  chunking_strategy: string;
  jd_quality: "ok" | "weak"; // NEW
  structured_skills: string[]; // NEW
};
```

기존 `AnalyzeResponse` 타입이 types.ts에 없으면 위 전체를 추가. 있으면 두 필드만 append.

- [ ] **Step 0.5: 프론트 타입 체크**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
npm --prefix frontend run build 2>&1 | tail -20
```
예상: Build succeeded, no TypeScript errors.

- [ ] **Step 0.6: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/schemas.py frontend/lib/types.ts
git commit -m "feat(schema): add coverage per skill, jd_quality, structured_skills to AnalyzeResponse"
```

---

## Task 1: Area A — 잡코리아 RSC skills 파싱

**Files:**
- Modify: `backend/app/services/text_extractor.py`
- Create: `backend/tests/fixtures/` (3개 HTML fixture)
- Modify: `backend/tests/test_text_extractor.py`

- [ ] **Step 1.1: 실제 공고 HTML fetch — RSC 패러다임 사전 검증 (HARD GATE)**

> ⚠️ **합성 fixture 금지.** 합성 HTML로 자신의 regex를 테스트하면 실제 잡코리아 구조가 다를 때 "테스트 그린, 제품 BROKEN" 상태가 된다. 실제 fetch가 실패하면 STOP하고 사용자에게 보고.

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
mkdir -p backend/tests/fixtures
python3 -c "
import re, json, sys
from urllib.request import Request, urlopen

URLS = {
    'jobkorea_43134476.html': 'https://www.jobkorea.co.kr/Recruit/GI_Read/43134476',  # 백엔드(Node.js/NoSQL/Go)
    'jobkorea_48391099.html': 'https://www.jobkorea.co.kr/Recruit/GI_Read/48391099',  # 백엔드(JAVA/Spring)
    'jobkorea_49244543.html': 'https://www.jobkorea.co.kr/Recruit/GI_Read/49244543',  # AI마케팅
}

def verify_rsc(html, expected_skills, fname):
    chunks = re.findall(r'self\.__next_f\.push\(\[\d+,(\"(?:[^\"\\\\]|\\\\.)*\")\]\)', html)
    payload = ''
    for c in chunks:
        try: payload += json.loads(c)
        except Exception: pass
    skills = re.findall(r'\{\"name\":\"([^\"]+)\",\"rank\":\d+,\"manualInput\":(?:true|false),\"skillTypeCode\":\"HARD_SKILL\"\}', payload)
    wf_m = re.search(r'\"workFields\":\[\"([^\"]+)\"', payload)
    ok = all(s in skills for s in expected_skills)
    print(f'[{fname}] chunks={len(chunks)} payload_len={len(payload)} skills={skills} workField={wf_m.group(1) if wf_m else None} OK={ok}')
    if not ok:
        print(f'  EXPECTED {expected_skills} — 실제 구조가 spec과 다름. STOP!')
        sys.exit(1)

failed = []
for fname, url in URLS.items():
    path = f'backend/tests/fixtures/{fname}'
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})
        data = urlopen(req, timeout=20).read()
        open(path, 'wb').write(data)
        print(f'saved {fname}: {len(data)} bytes')
    except Exception as e:
        failed.append((fname, str(e)))

if failed:
    print('FETCH FAILED:')
    for fname, err in failed: print(f'  {fname}: {err}')
    print()
    print('STOP — 실제 fixture 없이 진행 금지. 네트워크 접근 불가 환경이면 사용자에게 보고.')
    sys.exit(1)

# RSC 구조 검증 — spec 실측값과 대조
verify_rsc(open('backend/tests/fixtures/jobkorea_43134476.html').read(), ['Node.js', 'Go', 'NoSQL'], 'jobkorea_43134476.html')
verify_rsc(open('backend/tests/fixtures/jobkorea_48391099.html').read(), ['JAVA', 'Spring Boot'], 'jobkorea_48391099.html')
verify_rsc(open('backend/tests/fixtures/jobkorea_49244543.html').read(), ['Python', 'LLMOps', 'AI Agent'], 'jobkorea_49244543.html')
print('ALL RSC VERIFICATION PASSED — fixtures are from real HTML')
"
```

**실패 케이스별 대응:**
- `sys.exit(1)` (skills mismatch): RSC payload 구조가 spec과 다름 → **실제 payload를 덤프해 regex 재작성 후 재시도**
- `FETCH FAILED` (HTTP/네트워크): → **사용자에게 보고 후 STOP. 합성 fixture 생성 절대 금지**

- [ ] **Step 1.2: fixture 파싱 확인 (텍스트 확인)**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import re, json
html = open('backend/tests/fixtures/jobkorea_49244543.html').read()
chunks = re.findall(r'self\.__next_f\.push\(\[\d+,(\"(?:[^\"\\\\]|\\\\.)*\")\]\)', html)
payload = ''
for c in chunks:
    try:
        payload += json.loads(c)
    except Exception:
        pass
print('payload length:', len(payload))
pairs = re.findall(r'\{\"name\":\"([^\"]+)\",\"rank\":\d+,\"manualInput\":(?:true|false),\"skillTypeCode\":\"HARD_SKILL\"\}', payload)
print('skills:', pairs)
m = re.search(r'\"workFields\":\[\"([^\"]+)\"', payload)
print('workField:', m.group(1) if m else None)
"
```
예상 출력:
```
payload length: <양수>
skills: ['Python', 'LLMOps', 'ChatGPT', 'AI Agent', 'RPA', 'Node.js', 'Notion', 'Slack', 'API']  # 또는 실제 공고값
workField: AI 마케팅 자동화 엔지니어
```

- [ ] **Step 1.3: text_extractor.py 변경 — TextExtractionResult에 필드 추가**

`backend/app/services/text_extractor.py`에서 `TextExtractionResult` 데이터클래스를 찾아 수정:

```python
@dataclass(frozen=True)
class TextExtractionResult:
    text: str
    source_type: str
    extractor: str
    warnings: list[str]
    structured_skills: list[str] = field(default_factory=list)  # NEW
    job_title: str | None = None                                 # NEW
```

`field` import 추가가 필요하면:
```python
from dataclasses import dataclass, field
```

- [ ] **Step 1.4: text_extractor.py — 잡코리아 RSC 헬퍼 함수 추가**

파일 끝(또는 `extract_url` 함수 직전)에 추가:

```python
def _decode_jobkorea_rsc(html: str) -> str:
    """self.__next_f.push([N, "...JSON..."]) 청크들을 합쳐 RSC 페이로드 반환."""
    chunks = re.findall(r'self\.__next_f\.push\(\[\d+,("(?:[^"\\]|\\.)*")\]\)', html)
    out = []
    for c in chunks:
        try:
            out.append(json.loads(c))
        except Exception:
            pass
    return "".join(out)


def _extract_jobkorea_skills(payload: str) -> list[str]:
    """RSC 페이로드에서 HARD_SKILL name 목록 추출 (순서 유지, 중복 제거)."""
    pairs = re.findall(
        r'\{"name":"([^"]+)","rank":\d+,"manualInput":(?:true|false),"skillTypeCode":"HARD_SKILL"\}',
        payload,
    )
    seen: set[str] = set()
    result: list[str] = []
    for name in pairs:
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _extract_jobkorea_workfield(payload: str) -> str | None:
    """RSC 페이로드에서 첫 번째 workField(직무명) 추출."""
    m = re.search(r'"workFields":\["([^"]+)"', payload)
    return m.group(1) if m else None
```

`import json`이 이미 있는지 확인. 없으면 파일 상단에 추가.

- [ ] **Step 1.5: text_extractor.py — extract_url 잡코리아 분기 추가**

기존 `extract_url` 함수 내부에서 `urlopen` 이후 결과를 반환하기 직전 위치에 잡코리아 분기를 추가. 현재 `extract_url`의 반환문 직전에:

```python
def extract_url(url: str, *, timeout_seconds: int = 10, max_bytes: int = 2_000_000) -> TextExtractionResult:
    # ... 기존 HTTP 요청 코드 ...
    html_str = _decode_html(raw, content_type)

    # ── 잡코리아 RSC 분기 ─────────────────────────────────────────────
    from urllib.parse import urlparse as _urlparse
    host = _urlparse(url).hostname or ""
    if host.endswith("jobkorea.co.kr"):
        payload = _decode_jobkorea_rsc(html_str)
        skills = _extract_jobkorea_skills(payload)
        job_title = _extract_jobkorea_workfield(payload)
        visible = clean_text(_VisibleTextParser.parse(html_str))
        if skills:
            return TextExtractionResult(
                text=visible or f"[잡코리아 공고] {job_title or ''}",
                source_type="url",
                extractor="jobkorea_rsc",
                warnings=[],
                structured_skills=skills,
                job_title=job_title,
            )
        else:
            return TextExtractionResult(
                text=visible,
                source_type="url",
                extractor="jobkorea_meta_only",
                warnings=[
                    "이 공고에서 구조화된 기술 정보를 찾지 못했습니다. "
                    "본문을 직접 붙여넣어 주세요."
                ],
                structured_skills=[],
                job_title=job_title,
            )
    # ── 기존 반환 ────────────────────────────────────────────────────
    return TextExtractionResult(
        text=clean_text(_VisibleTextParser.parse(html_str)),
        source_type="url",
        extractor="url",
        warnings=[],
    )
```

`_VisibleTextParser.parse`가 실제 함수/클래스 이름인지 확인. 파일 내에서 실제로 사용하는 이름으로 교체.

- [ ] **Step 1.6: 실제 RSC 파싱 동작 확인**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import sys; sys.path.insert(0, 'backend')
from app.services.text_extractor import _decode_jobkorea_rsc, _extract_jobkorea_skills, _extract_jobkorea_workfield
html = open('backend/tests/fixtures/jobkorea_49244543.html').read()
payload = _decode_jobkorea_rsc(html)
print('skills:', _extract_jobkorea_skills(payload))
print('workfield:', _extract_jobkorea_workfield(payload))
"
```
예상: `skills: ['Python', 'LLMOps', ...]` (공고에 맞게)

- [ ] **Step 1.7: test_text_extractor.py에 RSC 파싱 테스트 추가**

기존 `backend/tests/test_text_extractor.py`에 다음 테스트 클래스를 추가:

```python
class TestJobkoreaRscParsing(unittest.TestCase):
    """fixture HTML을 사용한 잡코리아 RSC 파싱 단위 테스트 (네트워크 의존 없음)."""

    FIXTURE_DIR = Path(__file__).parent / "fixtures"

    def _load(self, name: str) -> str:
        return (self.FIXTURE_DIR / name).read_text(encoding="utf-8")

    def test_skills_extracted_ai_posting(self) -> None:
        html = self._load("jobkorea_49244543.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertIn("Python", skills)
        self.assertIn("LLMOps", skills)
        self.assertIn("AI Agent", skills)
        self.assertIn("RPA", skills)
        # 순서 유지: Python이 첫 번째
        self.assertEqual(skills[0], "Python")

    def test_workfield_extracted_ai_posting(self) -> None:
        html = self._load("jobkorea_49244543.html")
        payload = _decode_jobkorea_rsc(html)
        title = _extract_jobkorea_workfield(payload)
        self.assertIsNotNone(title)
        self.assertIn("AI", title)

    def test_skills_extracted_backend_nodejs(self) -> None:
        html = self._load("jobkorea_43134476.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertIn("Node.js", skills)
        self.assertIn("Go", skills)
        self.assertIn("NoSQL", skills)

    def test_skills_extracted_backend_java(self) -> None:
        html = self._load("jobkorea_48391099.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertIn("JAVA", skills)
        self.assertIn("Spring Boot", skills)

    def test_no_duplicate_skills(self) -> None:
        html = self._load("jobkorea_49244543.html")
        payload = _decode_jobkorea_rsc(html)
        skills = _extract_jobkorea_skills(payload)
        self.assertEqual(len(skills), len(set(skills)))

    def test_hh_posting_returns_warning(self) -> None:
        """RSC 없는 HTML → warnings에 안내 메시지."""
        html_no_rsc = "<html><body><p>헤드헌팅 공고 본문</p></body></html>"
        payload = _decode_jobkorea_rsc(html_no_rsc)
        skills = _extract_jobkorea_skills(payload)
        self.assertEqual(skills, [])
```

imports 상단에 추가:
```python
from pathlib import Path
from app.services.text_extractor import _decode_jobkorea_rsc, _extract_jobkorea_skills, _extract_jobkorea_workfield
```

- [ ] **Step 1.8: 테스트 실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_text_extractor -v 2>&1 | tail -20
```
예상: 신규 6개 포함 테스트 모두 OK.

- [ ] **Step 1.9: 전체 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```
예상: OK (46+ 테스트)

- [ ] **Step 1.10: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/services/text_extractor.py backend/tests/fixtures/ backend/tests/test_text_extractor.py
git commit -m "feat(extractor): parse jobkorea RSC skills array; add fixture-based unit tests"
```

---

## Task 2: Area B — skills 명명 정규화 (aliases 확장)

**Files:**
- Modify: `backend/app/services/c_part/skill_taxonomy.json`

- [ ] **Step 2.1: skill_taxonomy.json aliases 확장**

`skill_taxonomy.json`의 `"aliases"` 객체를 열고 다음 항목들이 없으면 추가:

```json
{
  "aliases": {
    "java": "Java",
    "JAVA": "Java",
    "restful api": "REST API",
    "restful": "REST API",
    "rest api": "REST API",
    "rest": "REST API",
    "Restful API": "REST API",
    "mssql": "MSSQL",
    "ms-sql": "MSSQL",
    "MS-SQL": "MSSQL",
    "nodejs": "Node.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "go": "Go",
    "golang": "Go",
    "GoLang": "Go",
    "nosql": "NoSQL",
    "chatgpt": "ChatGPT",
    "gpt": "ChatGPT",
    "llmops": "LLMOps",
    "llm ops": "LLMOps",
    "llm-ops": "LLMOps",
    "ai agent": "AI Agent",
    "rpa": "RPA",
    "langchain": "LangChain",
    "lang chain": "LangChain",
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",
    "mysql": "MySQL",
    "oracle": "Oracle"
  }
}
```

기존 aliases 항목과 병합 (덮어쓰기 아님).

- [ ] **Step 2.2: skill_taxonomy.json skills 신규 직군 추가**

`"skills"` 섹션의 `"ai"` 배열에 다음이 없으면 추가:
- `"LLMOps"`, `"AI Agent"`, `"LangChain"`, `"ChatGPT"`, `"RAG"`, `"Vector DB"`, `"Prompt Engineering"`

  > **ChatGPT 반드시 포함**: 49244543 공고의 성공 기준 #1에 ChatGPT가 명시됨. `_filter_analyzable_skills` 화이트리스트는 taxonomy를 기준으로 하므로, 여기 없으면 ChatGPT가 분석 대상에서 자동 제외됨.

`"backend"` 배열에 다음이 없으면 추가:
- `"Go"`, `"NoSQL"`, `"MSSQL"`, `"Oracle"`, `"gRPC"`, `"Kafka"`, `"RPA"`

- [ ] **Step 2.3: normalize_skill_name 동작 확인**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import sys; sys.path.insert(0, 'backend')
from app.services.c_part.pipeline import normalize_skill_name
tests = [('JAVA', 'Java'), ('Restful API', 'REST API'), ('golang', 'Go'), ('llmops', 'LLMOps'), ('ai agent', 'AI Agent')]
for raw, expected in tests:
    got = normalize_skill_name(raw)
    status = '✅' if got == expected else '❌'
    print(f'{status} {raw!r} → {got!r} (expected {expected!r})')
"
```
예상: 5개 모두 ✅. ❌가 있으면 aliases 오타 수정 후 재시도.

`normalize_skill_name`이 `pipeline.py`에 없으면 taxonomy의 aliases를 읽는 함수가 어디 있는지 확인. `skill_analyzer.py`나 `job_label_mapping.py`에 있을 수 있음. 실제 함수 이름으로 교체.

- [ ] **Step 2.4: 테스트 실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```
예상: OK (기존 수 이상)

- [ ] **Step 2.5: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/services/c_part/skill_taxonomy.json
git commit -m "feat(taxonomy): add aliases for JAVA→Java, Restful API→REST API, Go/LLMOps/AI Agent etc; expand ai/backend skills"
```

---

## Task 3: Coverage BASELINE/STRONG 측정 스크립트

**Files:**
- Create: `backend/tools/measure_coverage_baseline.py`

이 스크립트는 "맨 스킬 단어 → 지원자 문장" sim 분포를 측정해 BASELINE/STRONG 값을 결정한다. advisor 지적 4번 대응.

- [ ] **Step 3.1: 측정 스크립트 작성**

```python
# backend/tools/measure_coverage_baseline.py
"""
"맨 스킬 단어 → 지원자 문장" 코사인 유사도 분포 측정.
coverage 재설계(Task 4)의 BASELINE/STRONG 값을 실측으로 결정한다.

실행:
  PYTHONPATH=backend .venv/bin/python backend/tools/measure_coverage_baseline.py

출력:
  각 케이스별 sim 값 + 권장 BASELINE/STRONG 제안
"""
from __future__ import annotations

import sys
sys.path.insert(0, "backend")

import numpy as np
from app.services.c_part.pipeline import _model, _encode  # 또는 실제 모델 로딩 경로

# 실제 보유 기술 문장 샘플 (이상적 케이스 — "definitely matches")
OWNED_PAIRS = [
    ("Python", "Python으로 데이터 파이프라인을 구축하고 FastAPI 백엔드를 개발했습니다."),
    ("Docker", "Docker와 docker-compose로 로컬 개발환경 및 CI 파이프라인을 구성했습니다."),
    ("React", "React와 TypeScript로 대시보드 SPA를 개발했습니다."),
    ("Node.js", "Node.js Express로 REST API를 설계하고 배포했습니다."),
    ("LLMOps", "LLMOps 워크플로우를 구축하여 LLM 모델 버전 관리 및 평가를 자동화했습니다."),
    ("AI Agent", "LangChain 기반 AI Agent를 개발해 자동화 태스크를 처리했습니다."),
]

# 무관한 문장 (false positive 위험 케이스 — BASELINE 아래여야 함)
UNOWNED_PAIRS = [
    ("Python", "Excel과 PowerPoint로 보고서를 작성했습니다."),
    ("Docker", "팀 미팅 일정을 조율하고 회의록을 작성했습니다."),
    ("LLMOps", "홍보 콘텐츠를 SNS에 게시하고 마케팅 캠페인을 진행했습니다."),
]

# 경계 케이스 — 단순 언급 (partial 구간 예상)
PARTIAL_PAIRS = [
    ("Docker", "Docker에 대한 기본적인 개념을 이해하고 있으며 팀에서 사용하는 것을 보았습니다."),
    ("React", "React 스터디에 참여했고 기초 문법을 공부했습니다."),
    ("LLMOps", "LLMOps 관련 유튜브 영상을 시청하고 개념을 파악했습니다."),
]


def main() -> None:
    print("[측정] Ko-SRoBERTa 로딩 중...")
    # 모델 인코딩 함수 가져오기 — pipeline.py 내부 _encode 또는 model.encode 사용
    try:
        from app.services.c_part.pipeline import _encode as encode_fn
    except ImportError:
        print("ERROR: _encode를 pipeline.py에서 가져오지 못했습니다.")
        print("pipeline.py 내부에서 실제 encode 함수 이름을 확인하세요.")
        sys.exit(1)

    print("\n=== OWNED (충족 케이스) — STRONG 후보 ===")
    owned_sims = []
    for skill, sent in OWNED_PAIRS:
        vecs = encode_fn([skill, sent])
        sim = float(np.dot(vecs[0], vecs[1]) / (np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[1]) + 1e-9))
        owned_sims.append(sim)
        print(f"  sim={sim:.3f}  skill={skill!r}  sent={sent[:50]!r}...")

    print("\n=== UNOWNED (무관 케이스) — BASELINE 위 아니어야 함 ===")
    unowned_sims = []
    for skill, sent in UNOWNED_PAIRS:
        vecs = encode_fn([skill, sent])
        sim = float(np.dot(vecs[0], vecs[1]) / (np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[1]) + 1e-9))
        unowned_sims.append(sim)
        print(f"  sim={sim:.3f}  skill={skill!r}  sent={sent[:50]!r}...")

    print("\n=== PARTIAL (경계 케이스) — BASELINE~STRONG 사이 예상 ===")
    partial_sims = []
    for skill, sent in PARTIAL_PAIRS:
        vecs = encode_fn([skill, sent])
        sim = float(np.dot(vecs[0], vecs[1]) / (np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[1]) + 1e-9))
        partial_sims.append(sim)
        print(f"  sim={sim:.3f}  skill={skill!r}  sent={sent[:50]!r}...")

    # ── 권장값 계산 ──────────────────────────────────────────────────
    print("\n=== 권장 BASELINE/STRONG ===")
    # BASELINE: unowned의 max + 약간의 여유 (false positive 차단)
    baseline_candidate = max(unowned_sims) + 0.03 if unowned_sims else 0.25
    # STRONG: owned의 p25 (하위 25% 충족 케이스도 owned로 분류되도록)
    strong_candidate = float(np.percentile(owned_sims, 25)) if owned_sims else 0.55

    print(f"  권장 BASELINE = {baseline_candidate:.3f}  (unowned_max={max(unowned_sims):.3f}+0.03)")
    print(f"  권장 STRONG   = {strong_candidate:.3f}  (owned_p25={float(np.percentile(owned_sims, 25)):.3f})")
    print(f"  EXP_BONUS     = 15 (경험 동사 보너스 — 기존 유지)")
    print()
    print("  → pipeline.py Task 4에서 BASELINE/STRONG을 위 측정값으로 설정하세요.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3.2: 측정 스크립트 실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python backend/tools/measure_coverage_baseline.py 2>&1 | grep -v "^Loading\|^WARNING\|^\\[C파트\\] 모델\|^\\[C파트\\] 임베딩\|^\\[C파트\\] 최초"
```

**`_encode` 함수가 없을 경우**: pipeline.py에서 실제로 임베딩을 생성하는 함수명을 찾아 스크립트를 수정:
```bash
grep -n "def _encode\|def encode\|model.encode\|_model\." backend/app/services/c_part/pipeline.py | head -10
```

- [ ] **Step 3.3: 측정 결과 기록**

출력에서 `권장 BASELINE`, `권장 STRONG` 값을 읽어 **이 계획 문서 내 Task 4에 사용할 실측값으로 기록**. 예시 (실제 실행 후 대체):

```
실측 결과:
  BASELINE = 0.28  (unowned_max + 0.03)
  STRONG   = 0.52  (owned_p25)
  EXP_BONUS = 15
```

Task 4에서 이 값을 상수로 사용.

- [ ] **Step 3.4: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/tools/measure_coverage_baseline.py
git commit -m "tools: add coverage baseline measurement script for BASELINE/STRONG calibration"
```

---

## Task 4: Area D — coverage 단일 기준 재설계

**Files:**
- Modify: `backend/app/services/c_part/pipeline.py`

**전제**: Task 3에서 측정한 BASELINE/STRONG 실측값을 사용. 아래 코드에서 `BASELINE=0.28`, `STRONG=0.52`는 예시값 — 실제 측정값으로 교체.

- [ ] **Step 4.1: coverage 상수 추가**

`pipeline.py` 상단의 상수 블록(THR_OWNED_SKILL 등 근처)에 추가:

```python
# ── coverage 재설계 상수 (Task 3 측정값으로 교체) ─────────────────────
COV_BASELINE   = 0.28   # 이 이하 sim → coverage 0 (Task 3 측정 후 갱신)
COV_STRONG     = 0.52   # 이 이상 sim → coverage 100 (Task 3 측정 후 갱신)
COV_EXP_BONUS  = 15     # 경험 동사 있을 때 coverage 보너스
COV_OWNED_THR  = 70     # coverage >= 이 값 → owned
COV_PARTIAL_LO = 40     # 40 <= coverage < 70 → partial
# coverage < 40 → missing
```

- [ ] **Step 4.2: _compute_coverage 헬퍼 함수 추가**

`_gap_level` 함수 바로 아래에 추가:

```python
def _compute_coverage(best_sim: float, has_exp_verb: bool = False) -> float:
    """
    코사인 유사도 → coverage(0~100) 변환.
    coverage = clamp((sim - BASELINE) / (STRONG - BASELINE), 0, 1) * 100 + exp_bonus
    """
    raw = (best_sim - COV_BASELINE) / max(COV_STRONG - COV_BASELINE, 1e-6)
    cov = max(0.0, min(1.0, raw)) * 100.0
    if has_exp_verb:
        cov = min(100.0, cov + COV_EXP_BONUS)
    return round(cov, 1)


def _coverage_level(coverage: float) -> tuple[str, str]:
    """coverage 값 → (분류명, gap_level) 반환."""
    if coverage >= COV_OWNED_THR:
        return "owned", "낮음"
    elif coverage >= COV_PARTIAL_LO:
        return "partial", "중간"
    else:
        return "missing", "높음"
```

- [ ] **Step 4.3: _compute_gap에 coverage 반환 추가**

기존 `_compute_gap` 함수를 찾아 coverage도 함께 반환하도록 수정:

기존:
```python
def _compute_gap(source_sent, best_cand, importance):
    # ... 기존 로직 ...
    gap_score = max(round((1.0 - cand_sim) * 100), 0)
    # ...
    return gap_score, evidence
```

수정:
```python
def _compute_gap(source_sent, best_cand, importance):
    # ... 기존 로직(cand_sim 계산 포함) 유지 ...
    gap_score = max(round((1.0 - cand_sim) * 100), 0)
    # NEW: coverage 계산
    has_exp = bool(re.search("|".join(EXP_VERB_PATS), best_cand or "", re.IGNORECASE))
    coverage = _compute_coverage(cand_sim, has_exp_verb=has_exp)
    # ...
    return gap_score, evidence, coverage
```

`EXP_VERB_PATS`는 파이프라인 내 경험 동사 패턴 상수명 — 실제 이름 확인 후 교체.

- [ ] **Step 4.4: 6.5 분류 로직을 coverage 기반으로 교체**

pipeline.py 내부 "6.5 owned / partial / gap 완전 분리" 블록을 찾아 coverage 기반으로 재작성:

```python
# ── 6.5 coverage 기반 owned / partial / missing 분리 ─────────────────
# coverage ≥ 70 → owned, 40~69 → partial, < 40 → missing
# gap_score = 100 - coverage (하위 호환)
owned_skills_out = []
partial_skills_out = []
missing_skills_out = []
skill_coverage_map: dict[str, float] = {}   # ← Task 4.5 fit_score 계산에 사용
importance_map_local: dict[str, str] = {}   # ← Task 4.5 fit_score 계산에 사용

for skill_item in skill_gaps_raw:  # skill_gaps_raw = 기존 gap 계산 결과
    coverage = skill_item.get("coverage", 0.0)
    cat, _ = _coverage_level(coverage)
    gap_score = round(100 - coverage)
    gap_level = _gap_level(gap_score)
    importance = skill_item.get("importance", "필수")

    skill_coverage_map[skill_item["skill"]] = coverage
    importance_map_local[skill_item["skill"]] = importance

    if cat == "owned":
        owned_skills_out.append({
            "skill": skill_item["skill"],
            "evidence": [{"text": skill_item.get("evidence", ""), "source": "candidate"}],
        })
    elif cat == "partial":
        partial_skills_out.append({
            "skill": skill_item["skill"],
            "evidence": skill_item.get("evidence", ""),
            "evidence_strength": "partial",
            "gap_score": gap_score,
            "gap_level": gap_level,
            "importance": importance,
            "note": f"충족도 {coverage:.0f}%",
            "coverage": coverage,
        })
    else:  # missing
        missing_skills_out.append({
            "skill": skill_item["skill"],
            "gap_score": gap_score,
            "gap_level": gap_level,
            "importance": importance,
            "evidence": skill_item.get("evidence", "관련 경험 문장 미확인"),
            "coverage": coverage,
        })
```

실제 파이프라인 내 변수명은 파일을 읽고 확인 후 교체.

- [ ] **Step 4.5: _compute_fit_score를 coverage 평균 기반으로 재설계**

기존 `_compute_fit_score` 함수를 대체:

```python
def _compute_fit_score(
    required_skills: list[str],
    skill_coverage_map: dict[str, float],  # skill → coverage(0~100)
    importance_map: dict[str, str],        # skill → "필수" | "우대"
) -> float:
    """
    fit_score = 필수그룹 평균coverage × 0.7 + 우대그룹 평균coverage × 0.3
    없는 그룹은 100점 만점으로 처리하지 않음 — 존재하는 그룹으로만 재배분.
    """
    required_covs = [skill_coverage_map.get(s, 0.0) for s in required_skills if importance_map.get(s) == "필수"]
    preferred_covs = [skill_coverage_map.get(s, 0.0) for s in required_skills if importance_map.get(s) != "필수"]

    if required_covs and preferred_covs:
        score = (np.mean(required_covs) * 0.7 + np.mean(preferred_covs) * 0.3)
    elif required_covs:
        score = float(np.mean(required_covs))
    elif preferred_covs:
        score = float(np.mean(preferred_covs))
    else:
        score = 0.0

    return round(score, 1)
```

파이프라인 내 `fit_score = _compute_fit_score(...)` 호출부를 찾아 아래로 교체 (Task 4.4에서 생성한 `skill_coverage_map`, `importance_map_local` 사용):

```python
# ── 7. fit_score 산출 — coverage 기반 ────────────────────────────────
# importance_map_override: explicit_required_skills 모드에서 task 6.2가 세팅
_imp_map = importance_map_override if importance_map_override is not None else importance_map_local
fit_score = _compute_fit_score(
    required_skills=required_skills,
    skill_coverage_map=skill_coverage_map,
    importance_map=_imp_map,
)
```

- [ ] **Step 4.6: evidence 포맷 통일**

파이프라인 내 evidence 문자열 생성 부분을 찾아:

```python
# 기존 evidence 생성 → 새 포맷으로 교체
if best_candidate_sent:
    evidence = (
        f"공고 요구: {skill} / 내 자료 근거: '{best_candidate_sent[:120]}' "
        f"(충족도 {coverage:.0f}%)"
    )
else:
    evidence = f"공고 요구: {skill} / 관련 경험 문장 미확인"
```

- [ ] **Step 4.7: coverage 경계값 테스트 작성**

`backend/tests/test_c_part_pipeline.py`에 추가:

```python
# ── 경계값 분류 테스트 (수치 → 분류, 역산 없음) ────────────────────

def test_coverage_boundary_39_is_missing(self) -> None:
    from app.services.c_part.pipeline import _coverage_level
    self.assertEqual(_coverage_level(39.9)[0], "missing")

def test_coverage_boundary_40_is_partial(self) -> None:
    from app.services.c_part.pipeline import _coverage_level
    self.assertEqual(_coverage_level(40.0)[0], "partial")

def test_coverage_boundary_69_is_partial(self) -> None:
    from app.services.c_part.pipeline import _coverage_level
    self.assertEqual(_coverage_level(69.9)[0], "partial")

def test_coverage_boundary_70_is_owned(self) -> None:
    from app.services.c_part.pipeline import _coverage_level
    self.assertEqual(_coverage_level(70.0)[0], "owned")

def test_exp_bonus_caps_at_100(self) -> None:
    from app.services.c_part.pipeline import _compute_coverage, COV_STRONG
    cov = _compute_coverage(COV_STRONG + 0.1, has_exp_verb=True)
    self.assertLessEqual(cov, 100.0)

def test_zero_sim_gives_zero_coverage(self) -> None:
    from app.services.c_part.pipeline import _compute_coverage
    cov = _compute_coverage(0.0)
    self.assertEqual(cov, 0.0)

def test_compute_coverage_monotone(self) -> None:
    """sim 증가 → coverage 비감소."""
    from app.services.c_part.pipeline import _compute_coverage
    sims = [0.0, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]
    covs = [_compute_coverage(s) for s in sims]
    for i in range(len(covs) - 1):
        self.assertLessEqual(covs[i], covs[i + 1])
```

> **역산 테스트 제외 이유**: `sim_at_70 = BASELINE + 0.70*(STRONG-BASELINE)` → `_compute_coverage(sim_at_70) ≈ 70` 형태는 함수 자체의 수식을 다시 계산하는 것과 같아 무의미. 대신 단조 증가성 + 경계 분류 + 상한/하한으로 실질 동작 검증.

- [ ] **Step 4.8: 테스트 실행 — 신규 경계값 테스트만**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_c_part_pipeline.TestCPartPipeline.test_coverage_owned_at_70 backend.tests.test_c_part_pipeline.TestCPartPipeline.test_coverage_partial_at_55 -v 2>&1 | tail -15
```
예상: OK

- [ ] **Step 4.9: 전체 테스트 — 깨지는 케이스 기록 (커밋 아직 하지 말 것)**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | grep -E "FAIL|ERROR|OK"
```

깨지는 테스트 이름을 기록. Task 5에서 수정.

> **RED commit 방지**: Task 4 pipeline 변경으로 일부 테스트가 깨질 수 있음. 테스트가 모두 그린이 된 후 Task 5.5에서 한 번에 커밋. Task 4에서는 커밋하지 않음.

---

## Task 5: coverage 재설계 후 깨진 테스트 갱신

**Files:**
- Modify: `backend/tests/test_c_part_pipeline.py`
- Modify: `backend/tests/test_analyze_api.py`
- Modify: `backend/tests/test_product_schemas.py`

**전제**: Task 4 적용 후 실제로 깨진 테스트 목록을 보고 수정. mock 금지 — 실제 실행값으로 업데이트.

- [ ] **Step 5.1: test_fit_score_counts_partial_as_half 재측정 및 수정**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_c_part_pipeline.TestCPartPipeline.test_fit_score_counts_partial_as_half -v 2>&1 | tail -20
```

FAIL이면 새 `_compute_fit_score` 시그니처에 맞게 테스트 코드 재작성:

```python
def test_fit_score_counts_partial_as_half(self) -> None:
    """
    필수 2개 중 Docker(coverage=85,owned), AWS(coverage=50,partial) →
    fit_score = mean([85, 50]) × 0.7 (우대 없음) = 47.25 ≈ 47
    """
    from app.services.c_part.pipeline import _compute_fit_score
    required = ["Docker", "AWS"]
    coverage_map = {"Docker": 85.0, "AWS": 50.0}
    importance_map = {"Docker": "필수", "AWS": "필수"}
    score = _compute_fit_score(required, coverage_map, importance_map)
    # 필수만 있으면 (85+50)/2 = 67.5
    self.assertAlmostEqual(score, 67.5, delta=1.0)
```

**실제 측정값으로 교체**: 테스트가 어떤 값을 기대하는지 새 로직으로 직접 계산해서 delta 허용범위 내에서 통과하도록 설정.

- [ ] **Step 5.2: test_analyze_api.py 깨진 케이스 수정**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_analyze_api -v 2>&1 | grep -E "FAIL|ERROR" | head -10
```

FAIL/ERROR가 있으면 각 케이스의 새 기대값을 계산:
- `gap_score` 하드코딩 → `coverage` 기반 새 값으로 교체
- `fit_score` 하드코딩 → coverage 평균 기반 새 값으로 교체

패턴:
```python
# 기존 (task 4 이전)
self.assertEqual(body["partial_skills"][0]["gap_score"], 55)

# 새 기준 (coverage 기반 — 실측값으로 채움)
self.assertGreater(body["partial_skills"][0]["coverage"], 40)
self.assertLess(body["partial_skills"][0]["coverage"], 70)
```

- [ ] **Step 5.3: test_product_schemas.py 깨진 케이스 수정**

같은 방식으로 수정. `gap_score: 55` → `coverage: <실측범위>` 범위 assert로 교체.

- [ ] **Step 5.4: 전체 테스트 그린 확인**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```
예상: OK (기존 46 + 신규)

- [ ] **Step 5.5: 커밋 (Task 4 pipeline + Task 5 테스트 함께 — 그린 상태에서만)**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/services/c_part/pipeline.py backend/tests/
git commit -m "feat(coverage): single coverage metric; update tests to measured values; boundary tests"
```

---

## Task 6: Area C — explicit skills 주입 + relevance 필터 + classify_job 입력 보강

**Files:**
- Modify: `backend/app/services/c_part/pipeline.py`
- Modify: `backend/app/main.py`

- [ ] **Step 6.1: _filter_analyzable_skills 추가 (relevance 필터)**

`pipeline.py`에 추가:

```python
# ── relevance 필터 상수 ───────────────────────────────────────────────
# 화이트리스트: taxonomy skills 또는 추천DB에 매핑된 기술만 분석 대상
_WHITELIST_SKILLS: set[str] = {
    s.lower()
    for group in _TAXONOMY.get("skills", {}).values()
    for s in group
}

# 블랙리스트: 협업/일반 도구 (명시적 제외)
_BLACKLIST_SKILLS: set[str] = {
    "notion", "slack", "jira", "confluence", "figma",
    "api", "git", "github", "gitlab", "excel", "powerpoint",
    "google docs", "google sheets", "teams", "zoom",
}


def _filter_analyzable_skills(skills: list[str]) -> list[str]:
    """
    relevance 필터:
    1. 블랙리스트 제외 (Notion/Slack/API/Git 등 협업·일반 도구)
    2. 화이트리스트(taxonomy skills 배열)에 있는 기술만 분석 대상으로 포함
       (추천DB 매핑은 이 필터에서 확인하지 않음 — taxonomy가 단일 기준)
    3. 화이트리스트 미매핑 기술은 제외
       (caller가 structured_skills에는 별도 표시하므로 공고 투명성은 유지)
    """
    result = []
    for s in skills:
        if s.lower() in _BLACKLIST_SKILLS:
            continue
        if s.lower() in _WHITELIST_SKILLS:
            result.append(s)
        # taxonomy에 없는 기술 제외 — ChatGPT 등은 Task 2.2에서 taxonomy에 추가됨
    return result
```

- [ ] **Step 6.2: run_c_part_analysis에 explicit_required_skills 파라미터 추가**

함수 시그니처를 찾아 파라미터 추가:

```python
def run_c_part_analysis(
    jd_text: str,
    candidate_text: str,
    b_predicted_job: str,
    *,
    explicit_required_skills: list[str] | None = None,  # NEW
) -> dict:
```

함수 내부에서 required_skills 결정 분기:

```python
# ── 5. required_skills 결정 ────────────────────────────────────────
if explicit_required_skills is not None:
    required_skills = explicit_required_skills
    # explicit 모드: 잡코리아 skills 배열 직접 주입
    # importance는 전부 "필수"로 간주 (배열이 필수/우대 미구분)
    importance_map_override = {s: "필수" for s in required_skills}
else:
    required_skills = extract_required_skills(jd_text)  # 기존 sim 기반
    importance_map_override = None
```

이후 importance_map 사용 시 `importance_map_override`가 None이 아니면 우선 적용.

- [ ] **Step 6.3: main.py /analyze 핸들러 수정**

`backend/app/main.py`에서 `/analyze` 엔드포인트 핸들러를 찾아 수정:

```python
@app.post("/analyze")
async def analyze(...):
    # ... 기존 추출 코드 ...
    job_extracted = extract_url(url) if url else extract_text_input(text)

    explicit_required_skills = None
    classify_input = job_extracted.text  # 기본값

    if job_extracted.structured_skills:
        raw_skills = job_extracted.structured_skills
        norm_skills = [normalize_skill_name(s) for s in raw_skills]
        analyzable = _filter_analyzable_skills(norm_skills)
        explicit_required_skills = analyzable

        # BLOCK 1: classify_job 입력 보강 — 직무명+기술 신호를 앞에 배치
        signal = " ".join(filter(None, [job_extracted.job_title, *norm_skills]))
        classify_input = signal + "\n" + job_extracted.text

    c_result = run_c_part_analysis(
        jd_text=classify_input,
        candidate_text=candidate_text,
        b_predicted_job=predicted_job,
        explicit_required_skills=explicit_required_skills,
    )

    # ... 나머지 로직 ...

    # AnalyzeResponse 생성 시 structured_skills 포함
    return AnalyzeResponse(
        # ... 기존 필드 ...
        structured_skills=job_extracted.structured_skills,  # 공고 명시 전체 기술(표시용)
        # jd_quality는 Task 10에서 추가
    )
```

`normalize_skill_name`이 `main.py`에서 import 가능한지 확인. 없으면 적절한 위치에서 import.

- [ ] **Step 6.4: classify_job 입력 보강 단독 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import sys; sys.path.insert(0, 'backend')
from app.services.job_classifier import classify_job

# 기존 (메타 노이즈만)
old_input = '접수기간: ~2024-12-31 복지: 4대보험 위치: 서울 AI 마케팅 자동화 엔지니어'
# 새 (직무명+기술 보강)
new_input = 'AI 마케팅 자동화 엔지니어 Python LLMOps ChatGPT AI Agent RPA Node.js\n' + old_input

old_result = classify_job(old_input)
new_result = classify_job(new_input)

# classify_job은 JobClassification(predicted_job, job_probabilities) 반환
print('OLD predicted_job:', old_result.predicted_job)
print('OLD AI prob:', old_result.job_probabilities.get('AI/ML', old_result.job_probabilities))
print('NEW predicted_job:', new_result.predicted_job)
print('NEW AI prob:', new_result.job_probabilities.get('AI/ML', new_result.job_probabilities))
ai_label = next((k for k in new_result.job_probabilities if 'AI' in k or 'ML' in k), None)
if ai_label:
    old_ai = old_result.job_probabilities.get(ai_label, 0)
    new_ai = new_result.job_probabilities.get(ai_label, 0)
    print(f'AI prob: {old_ai:.3f} → {new_ai:.3f} (개선={new_ai > old_ai})')
"
```
예상: new_input의 AI 확률이 old_input보다 높고, `predicted_job`이 AI 계열로 안정.

- [ ] **Step 6.5: 전체 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```

- [ ] **Step 6.6: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/services/c_part/pipeline.py backend/app/main.py
git commit -m "feat(c-part): inject explicit skills from RSC; add relevance filter; boost classify_job input"
```

---

## Task 7: Area G — 추천자료 DB 확장 + URL liveness 검증

**Files:**
- Modify: `backend/app/data/learning_resources.csv`
- Modify: `backend/tools/audit_learning_resources.py` (liveness 체크 추가)

- [ ] **Step 7.1: 현재 DB resource_count 확인 및 컬럼 구조 파악**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import csv
rows = list(csv.DictReader(open('backend/app/data/learning_resources.csv')))
print('현재 rows:', len(rows))
print('컬럼:', list(rows[0].keys()))
print('기술 목록 샘플:', sorted({r['skill'] for r in rows})[:20])
"
```

- [ ] **Step 7.2: 신규 자료 행 추가**

`learning_resources.csv`에 다음 기술별 최소 3개 자료 추가. 각 행은 기존 컬럼 구조를 따름:

**LLMOps (ai 직군)**:
- 공식문서/가이드: `https://docs.bentoml.com/en/latest/` "BentoML LLMOps 공식 문서" (무료)
- 유튜브: `https://www.youtube.com/watch?v=Fquj2u7ay40` "LLMOps explained — practical guide" (무료)
- 강의: `https://learn.deeplearning.ai/courses/llmops` "DeepLearning.AI LLMOps" (무료)

**AI Agent (ai 직군)**:
- 공식문서: `https://python.langchain.com/docs/how_to/agent_executor/` "LangChain Agent Executor 공식 문서" (무료)
- 유튜브: `https://www.youtube.com/watch?v=DWUdGhRrv2c` "AI Agents 실전 구현" (무료)
- 강의: `https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/` "AI Agents in LangGraph" (무료)

**LangChain (ai 직군)**:
- 공식문서: `https://python.langchain.com/docs/introduction/` "LangChain 공식 문서" (무료)
- 유튜브: `https://www.youtube.com/watch?v=nAmC7SoVLd8` "LangChain Crash Course" (무료)

**Go (backend 직군)**:
- 공식문서: `https://go.dev/doc/` "Go 공식 문서 & Tour" (무료)
- 유튜브: `https://www.youtube.com/watch?v=un6ZyFkqFKo` "Go Programming Tutorial" (무료)
- 강의: `https://www.udemy.com/course/learn-how-to-code/` "Learn How To Code: Google's Go" (유료)

**NoSQL (backend 직군)**:
- 공식문서: `https://www.mongodb.com/docs/manual/` "MongoDB 공식 문서" (무료)
- 유튜브: `https://www.youtube.com/watch?v=ofme2o29ngU` "MongoDB Crash Course" (무료)
- 공식문서: `https://redis.io/docs/` "Redis 공식 문서" (무료)

**RPA (common)**:
- 공식문서: `https://docs.uipath.com/` "UiPath RPA 공식 문서" (무료)
- 유튜브: `https://www.youtube.com/watch?v=sGmFg8VRJIE` "RPA 입문 튜토리얼" (무료)

각 행의 `reason` 필드: `"잡코리아 공고 실측에서 자주 등장하는 요구 기술 — <기술명> 공식 학습 경로"`

```bash
# 기존 max id 확인
python3 -c "
import csv
rows = list(csv.DictReader(open('backend/app/data/learning_resources.csv')))
ids = [r['id'] for r in rows if r['id'].isdigit()]
print('max id:', max(int(i) for i in ids) if ids else 'N/A')
"
```

CSV에 새 행 추가 시 기존 max_id + 1부터 순번 부여.

- [ ] **Step 7.3: audit_learning_resources.py에 liveness 체크 로직 확인/추가**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
head -50 backend/tools/audit_learning_resources.py
```

HTTP 상태코드 확인이 없으면 추가:

```python
# audit_learning_resources.py에 없는 경우 추가
def check_liveness(url: str, timeout: int = 8) -> tuple[bool, int]:
    """URL이 2xx 응답하면 True 반환."""
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        resp = urlopen(req, timeout=timeout)
        return resp.status < 300, resp.status
    except HTTPError as e:
        return False, e.code
    except (URLError, Exception):
        return False, 0
```

- [ ] **Step 7.4: URL liveness 검증 실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py 2>&1 | tail -30
```

`DEAD` 또는 `error` 표시된 URL이 있으면 working URL로 교체 또는 해당 행 삭제 후 재실행. 죽은 링크가 포함된 커밋 금지.

- [ ] **Step 7.5: health endpoint resource_count 확인**

```bash
# 서버가 떠 있으면 확인
curl -s http://127.0.0.1:8010/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('resource_count:', d.get('resource_count'))" \
  || echo "(서버 미실행 — 로컬 파일 카운트)"

# 서버 없이 확인
python3 -c "
import csv
rows = list(csv.DictReader(open('backend/app/data/learning_resources.csv')))
print('resource_count:', len(rows))
"
```
목표: 110+ 행.

- [ ] **Step 7.6: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/data/learning_resources.csv backend/tools/audit_learning_resources.py
git commit -m "feat(db): expand learning resources to 110+ rows; add LLMOps/AI Agent/Go/NoSQL/RPA resources; verify URL liveness"
```

---

## Task 8: Area E — 로드맵 재설계 (distribute_weeks 버그 수정)

**Files:**
- Modify: `backend/app/services/roadmap_generator.py`
- Modify: `backend/tests/test_roadmap_generator.py`

- [ ] **Step 8.1: 현재 distribute_weeks 버그 확인**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import sys; sys.path.insert(0, 'backend')
# roadmap_generator 내 distribute_weeks 함수 직접 호출
from app.services.roadmap_generator import distribute_weeks  # 실제 함수명 확인 필요
result = distribute_weeks(['Python'], 4)  # 스킬 1개, 4주
print('goals:', [r.get('goal') for r in result])
print('bug?', len(set(r.get('goal') for r in result)) == 1)
"
```

- [ ] **Step 8.2: roadmap_generator.py 수정**

실제 함수 구현을 찾아 다음 로직으로 대체:

```python
PHASES = ["기초 개념·환경 설정", "핵심 기능 실습", "미니 프로젝트 적용", "정리·면접 대비"]


def distribute_weeks(
    skills: list[str],
    duration_weeks: int,
    skill_recommendations: dict[str, list[str]],  # skill → recommended_titles
) -> list[dict]:
    """
    skills를 duration_weeks 주차에 배분.
    - skills >= weeks: 주차당 1스킬 (상위 weeks개)
    - skills < weeks: 각 스킬에 연속 주차 + 주차 내 PHASES 차등
    - 스킬 1개/4주: 4주 모두 같은 스킬, goal/practice가 PHASES[i]로 달라짐
    """
    n_skills = min(len(skills), 5)  # cap 5
    skills = skills[:n_skills]
    weeks_out = []

    if n_skills == 0:
        return []

    if n_skills >= duration_weeks:
        # 주차당 1스킬
        for i in range(duration_weeks):
            skill = skills[i]
            titles = skill_recommendations.get(skill, [])
            weeks_out.append({
                "week": i + 1,
                "goal": f"{skill} {PHASES[0]}",
                "skills": [skill],
                "recommended_titles": titles[:2],
                "practice": f"{skill}로 간단한 예제 구현",
            })
    else:
        # 각 스킬에 연속 주차 배분
        weeks_per_skill = duration_weeks // n_skills
        extra = duration_weeks % n_skills
        week_num = 1
        for idx, skill in enumerate(skills):
            alloc = weeks_per_skill + (1 if idx < extra else 0)
            titles = skill_recommendations.get(skill, [])
            for j in range(alloc):
                phase_idx = min(j, len(PHASES) - 1)
                phase = PHASES[phase_idx]
                weeks_out.append({
                    "week": week_num,
                    "goal": f"{skill} — {phase}",
                    "skills": [skill],
                    "recommended_titles": titles[j * 1: j * 1 + 2] if titles else [],
                    "practice": f"{skill} {phase}: {'환경 구성 및 헬로월드' if j == 0 else '핵심 API 실습' if j == 1 else '미니 프로젝트 1개' if j == 2 else '개념 정리 + 기술면접 답변 초안'}",
                })
                week_num += 1

    return weeks_out
```

함수 시그니처가 바뀌면 호출부(`generate_roadmap` 등)도 함께 수정.

- [ ] **Step 8.3: 테스트 작성**

```python
# backend/tests/test_roadmap_generator.py에 추가
def test_single_skill_4weeks_goals_are_distinct(self) -> None:
    from app.services.roadmap_generator import distribute_weeks
    result = distribute_weeks(["Python"], 4, {"Python": ["파이썬 공식 문서", "Real Python"]})
    self.assertEqual(len(result), 4)
    goals = [r["goal"] for r in result]
    self.assertEqual(len(set(goals)), 4, f"goals must all differ, got {goals}")

def test_5skills_4weeks_uses_top_4(self) -> None:
    from app.services.roadmap_generator import distribute_weeks
    skills = ["Python", "Docker", "React", "Go", "NoSQL"]
    result = distribute_weeks(skills, 4, {})
    self.assertEqual(len(result), 4)
    covered = {r["skills"][0] for r in result}
    self.assertEqual(len(covered), 4)

def test_2skills_4weeks_each_gets_2weeks(self) -> None:
    from app.services.roadmap_generator import distribute_weeks
    result = distribute_weeks(["Python", "Docker"], 4, {})
    self.assertEqual(len(result), 4)
    python_weeks = sum(1 for r in result if "Python" in r["skills"])
    docker_weeks = sum(1 for r in result if "Docker" in r["skills"])
    self.assertEqual(python_weeks, 2)
    self.assertEqual(docker_weeks, 2)
```

- [ ] **Step 8.4: 테스트 실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_roadmap_generator -v 2>&1 | tail -15
```
예상: 신규 테스트 포함 OK.

- [ ] **Step 8.5: 전체 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```

- [ ] **Step 8.6: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/services/roadmap_generator.py backend/tests/test_roadmap_generator.py
git commit -m "fix(roadmap): distinct goals per week for 1-skill case; add PHASES-based progression tests"
```

---

## Task 9: Area F — 리포트 재작성

**Files:**
- Modify: `backend/app/services/report_generator.py`

- [ ] **Step 9.1: generate_product_report 현재 구조 파악**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
grep -n "def generate_product_report\|def generate\|evidence\|접수기간\|복지" backend/app/services/report_generator.py | head -20
```

- [ ] **Step 9.2: 리포트 생성 함수 재작성**

`generate_product_report` (또는 해당 함수명)을 찾아 다음 구조로 재작성:

```python
def generate_product_report(analysis_result: dict) -> str:
    """
    리포트 구조:
    ① 직무 분류 + 적합도
    ② 요구 N개 중 충족 X / 보완 Y / 부족 Z
    ③ 최우선 보완 1~2개 + coverage%
    ④ 로드맵 요약 (주차별 상이 반영)
    """
    predicted_job = analysis_result.get("predicted_job", "직무 미분류")
    fit_score = analysis_result.get("fit_score", 0)
    jd_quality = analysis_result.get("jd_quality", "ok")

    owned = analysis_result.get("owned_skills", [])
    partial = analysis_result.get("partial_skills", [])
    missing = analysis_result.get("missing_skills", [])
    roadmap = analysis_result.get("weekly_roadmap", [])

    # ① 직무·적합도
    lines = [
        f"## 직무 분석 결과",
        f"",
        f"**예측 직무**: {predicted_job}  |  **역량 적합도**: {fit_score:.0f}점",
        f"",
    ]

    if jd_quality == "weak":
        lines += [
            "⚠️ **이 공고에서 명확한 기술 요구를 찾지 못했습니다.** "
            "개발 직무 공고인지 확인하거나 본문을 직접 붙여넣어 주세요.",
            "",
        ]
        return "\n".join(lines)

    # ② 카운트
    total = len(owned) + len(partial) + len(missing)
    lines += [
        f"## 역량 충족 현황 (공고 요구 {total}개)",
        f"",
        f"- ✅ **충족** {len(owned)}개",
        f"- 🟡 **보완 필요** {len(partial)}개",
        f"- ❌ **부족** {len(missing)}개",
        f"",
    ]

    # ③ 최우선 보완 (missing 상위 2개)
    top_missing = sorted(missing, key=lambda x: x.get("gap_score", 100), reverse=True)[:2]
    if top_missing:
        lines.append("## 최우선 보완 역량")
        lines.append("")
        for item in top_missing:
            cov = item.get("coverage", 0)
            lines.append(f"- **{item['skill']}** — 현재 충족도 {cov:.0f}%")
        lines.append("")

    # ④ 로드맵 요약
    if roadmap:
        lines.append("## 학습 로드맵 요약")
        lines.append("")
        for week_item in roadmap:
            lines.append(f"**{week_item['week']}주차**: {week_item.get('goal', '')}")
        lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 9.3: 리포트 노이즈 테스트**

```python
# backend/tests/test_report_generator.py에 추가 (파일 없으면 생성)
def test_report_no_noise_text(self) -> None:
    """evidence 원문(접수기간/복지/주소)이 리포트에 포함되지 않는다."""
    from app.services.report_generator import generate_product_report
    result = {
        "predicted_job": "AI/ML 엔지니어",
        "fit_score": 65,
        "jd_quality": "ok",
        "owned_skills": [{"skill": "Python", "coverage": 80}],
        "partial_skills": [],
        "missing_skills": [{"skill": "LLMOps", "gap_score": 70, "coverage": 30}],
        "weekly_roadmap": [{"week": 1, "goal": "LLMOps 기초"}],
    }
    report = generate_product_report(result)
    self.assertNotIn("접수기간", report)
    self.assertNotIn("복지", report)
    self.assertNotIn("주소", report)

def test_report_weak_jd_no_fit_score(self) -> None:
    """jd_quality=weak이면 fit_score·격차 단정 표현이 없고 경고 문구가 있다."""
    from app.services.report_generator import generate_product_report
    result = {
        "predicted_job": "미분류",
        "fit_score": 77,
        "jd_quality": "weak",
        "owned_skills": [],
        "partial_skills": [],
        "missing_skills": [],
        "weekly_roadmap": [],
    }
    report = generate_product_report(result)
    self.assertIn("명확한 기술 요구를 찾지 못했습니다", report)
    # weak일 때 "77점" 같은 수치 단정 없어야 함
    self.assertNotIn("77점", report)
```

- [ ] **Step 9.4: 테스트 실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_report_generator -v 2>&1 | tail -15
```

- [ ] **Step 9.5: 전체 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```

- [ ] **Step 9.6: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/services/report_generator.py backend/tests/test_report_generator.py
git commit -m "refactor(report): remove evidence noise; coverage-based structure; weak JD warning"
```

---

## Task 10: Area H — jd_quality 경고 + 결과 suppress

**Files:**
- Modify: `backend/app/main.py`
- Modify: `frontend/app/page.tsx`

- [ ] **Step 10.1: main.py — jd_quality 판정 로직 추가**

`/analyze` 핸들러에서 `AnalyzeResponse` 반환 직전:

```python
# jd_quality 판정
structured_skills = job_extracted.structured_skills
required_count = len(c_result.get("required_skills", []))
jd_quality: str
if not structured_skills and required_count < 3:
    jd_quality = "weak"
else:
    jd_quality = "ok"

return AnalyzeResponse(
    # ... 기존 필드 ...
    jd_quality=jd_quality,
    structured_skills=structured_skills,
)
```

- [ ] **Step 10.2: jd_quality 경고 배너 테스트 작성**

```python
# backend/tests/test_analyze_api.py에 추가
def test_weak_jd_sets_jd_quality_field(self) -> None:
    """HH/비표준 공고 텍스트 입력 시 jd_quality=weak 반환."""
    # 기술 요구가 거의 없는 짧은 텍스트
    payload = {
        "job_posting": {"source_type": "text", "text": "채용 공고입니다. 우리 회사에서 일할 분을 모집합니다."},
        "candidate_materials": [{"source_type": "text", "label": "이력서", "text": "Python 개발 경험 3년, Django REST API 구축."}],
        "roadmap_preferences": {"duration_weeks": 4, "difficulty": "실무", "intensity": "보통"},
    }
    # 이 테스트는 실제 API 서버 없이 단위 수준에서 jd_quality 로직만 검증
    # 서버 통합 테스트는 Task 12에서 E2E로 검증
    from app.main import _determine_jd_quality  # 함수 분리 시
    quality = _determine_jd_quality(structured_skills=[], required_count=1)
    self.assertEqual(quality, "weak")

    quality_ok = _determine_jd_quality(structured_skills=["Python"], required_count=3)
    self.assertEqual(quality_ok, "ok")
```

`_determine_jd_quality` 함수를 `main.py`에 분리해 단위 테스트 가능하게:

```python
# backend/app/main.py
def _determine_jd_quality(structured_skills: list[str], required_count: int) -> str:
    if not structured_skills and required_count < 3:
        return "weak"
    return "ok"
```

- [ ] **Step 10.3: frontend — 경고 배너 컴포넌트 추가**

`frontend/app/page.tsx`에서 `AnalyzeResponse` 렌더링 부분을 찾아 jd_quality=weak 시 배너 표시:

```tsx
{/* jd_quality 경고 배너 */}
{result.jd_quality === "weak" && (
  <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-amber-800 text-sm mb-4">
    ⚠️ 이 공고에서 명확한 기술 요구를 찾지 못했습니다.
    개발 직무 공고인지 확인하거나 본문을 직접 붙여넣어 주세요.
  </div>
)}

{/* weak일 때 결과 섹션을 흐리게 */}
<div className={result.jd_quality === "weak" ? "opacity-40 pointer-events-none" : ""}>
  {/* fit_score, 차트, 로드맵 기존 렌더링 */}
</div>
```

- [ ] **Step 10.4: 프론트 빌드 확인**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
npm --prefix frontend run build 2>&1 | tail -10
```
예상: Build succeeded.

- [ ] **Step 10.5: 전체 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```

- [ ] **Step 10.6: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add backend/app/main.py frontend/app/page.tsx
git commit -m "feat(quality): add jd_quality weak detection; frontend warning banner + opacity suppress"
```

---

## Task 11: Area I — 프론트 UI 개선

**Files:**
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/app/globals.css`

- [ ] **Step 11.1: 역량 격차 차트에 coverage% 노출**

차트/리스트에서 각 스킬 항목에 `coverage` 표시. 예:

```tsx
{/* 스킬 항목 렌더링 — PartialSkill 예시 */}
<div key={skill.skill} className="flex items-center gap-3 p-3 rounded-lg border">
  <span className="font-medium">{skill.skill}</span>
  <span className={`text-sm px-2 py-0.5 rounded-full ${
    skill.coverage >= 70 ? "bg-green-100 text-green-700" :
    skill.coverage >= 40 ? "bg-amber-100 text-amber-700" :
    "bg-red-100 text-red-700"
  }`}>
    충족도 {skill.coverage?.toFixed(0) ?? 0}%
  </span>
</div>
```

- [ ] **Step 11.2: 추천자료 카드에 reason 표시**

`ResourceRecommendation` 카드에서 `resource.reason` 필드가 있으면 표시:

```tsx
{rec.resource.reason && (
  <p className="text-xs text-gray-500 mt-1 italic">
    💡 {rec.resource.reason}
  </p>
)}
```

- [ ] **Step 11.3: structured_skills 섹션 추가 (공고 명시 전체 기술)**

분석 결과 상단에 공고가 명시한 기술 전체를 표시 (jd_quality=ok 이고 structured_skills 있을 때):

```tsx
{result.structured_skills?.length > 0 && (
  <div className="mb-4">
    <h3 className="text-sm font-semibold text-gray-600 mb-2">공고 명시 기술 전체</h3>
    <div className="flex flex-wrap gap-2">
      {result.structured_skills.map((s) => (
        <span key={s} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
          {s}
        </span>
      ))}
    </div>
  </div>
)}
```

- [ ] **Step 11.4: 프론트 빌드 + E2E**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
npm --prefix frontend run build 2>&1 | tail -5
npm --prefix frontend run e2e 2>&1 | tail -10
```
예상: Build OK, E2E 3종 그린.

- [ ] **Step 11.5: 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add frontend/app/page.tsx frontend/app/globals.css
git commit -m "feat(ui): show coverage% color tags on skills; resource reason; structured_skills display"
```

---

## Task 12: 최종 회귀 검증

서버가 떠있지 않으면 시작:
```bash
# tmux 세션 확인
tmux has-session -t nlp-backend-8010 2>/dev/null && echo "backend running" || echo "backend not running"
tmux has-session -t nlp-frontend-3010 2>/dev/null && echo "frontend running" || echo "frontend not running"
```

서버 미실행 시:
```bash
# 새 터미널에서
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
tmux new-session -d -s nlp-backend-8010 ".venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8010"
tmux new-session -d -s nlp-frontend-3010 "BACKEND_ORIGIN=http://127.0.0.1:8010 npm --prefix frontend run dev -- --hostname 127.0.0.1 --port 3010"
sleep 5
```

- [ ] **Step 12.1: 백엔드 전체 테스트**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests 2>&1 | tail -5
```
예상: OK

- [ ] **Step 12.2: 프론트 빌드 + E2E**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
npm --prefix frontend run build 2>&1 | tail -5
npm --prefix frontend run e2e 2>&1 | tail -10
```
예상: Build OK, E2E OK

- [ ] **Step 12.3: audit_learning_resources 재실행**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py 2>&1 | grep -E "DEAD|ERROR|total|resource_count"
```
예상: DEAD 0개, resource_count ≥ 110

- [ ] **Step 12.4: 3 공고 classify_job 회귀 체크 (BLOCK 1)**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import sys; sys.path.insert(0, 'backend')
from app.services.text_extractor import _decode_jobkorea_rsc, _extract_jobkorea_skills, _extract_jobkorea_workfield
from app.services.job_classifier import classify_job

for fname, expected_kw in [
    ('backend/tests/fixtures/jobkorea_49244543.html', 'AI'),
    ('backend/tests/fixtures/jobkorea_43134476.html', '백엔드'),
    ('backend/tests/fixtures/jobkorea_48391099.html', '백엔드'),
]:
    html = open(fname).read()
    payload = _decode_jobkorea_rsc(html)
    skills = _extract_jobkorea_skills(payload)
    title = _extract_jobkorea_workfield(payload)
    classify_input = f'{title or \"\"} {\" \".join(skills)}\n'
    result = classify_job(classify_input)
    top2 = sorted(result.job_probabilities.items(), key=lambda x: -x[1])[:2]
    status = '✅' if expected_kw in result.predicted_job else '❌'
    print(f'{status} {fname.split(\"/\")[-1]}: predicted={result.predicted_job!r} top2={top2}')
"
```
예상:
- 49244543: predicted='AI/ML 엔지니어' 계열 (혹은 AI 포함 label), AI 확률 1위, 2위와 차이 0.10+
- 43134476: predicted에 '백엔드' 포함, 확률 0.80+
- 48391099: predicted에 '백엔드' 포함, 확률 0.70+

- [ ] **Step 12.5: 텍스트 모드 직접 입력 회귀 체크 (BLOCK 1 비회귀)**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
python3 -c "
import sys; sys.path.insert(0, 'backend')
from app.services.job_classifier import classify_job

text_backend = 'Node.js Express로 REST API 개발. PostgreSQL, Redis 사용. AWS EC2 배포 경험.'
text_ai = 'LLM 기반 챗봇 파이프라인 구축. Python, LangChain, Vector DB 활용. MLOps 자동화.'

r_backend = classify_job(text_backend)
r_ai = classify_job(text_ai)

print('텍스트 백엔드:', r_backend.predicted_job, sorted(r_backend.job_probabilities.items(), key=lambda x:-x[1])[:2])
print('텍스트 AI:', r_ai.predicted_job, sorted(r_ai.job_probabilities.items(), key=lambda x:-x[1])[:2])
"
```
예상: 텍스트 모드도 이전과 동일하게 정상 분류 (입력 보강이 URL 경로에만 적용됨).

- [ ] **Step 12.6: 성공 기준 체크리스트**

```
[ ] 49244543 → required_skills에 MLflow 없음; Notion·Slack·API 없음
[ ] 49244543 → structured_skills에는 Notion·Slack·API 포함 (표시용)
[ ] evidence에 "접수기간"/"복지"/"주소" 텍스트 0
[ ] 4주 로드맵 goal 4개 상이
[ ] 추천 자료 카드에 reason 표시
[ ] 비개발 공고(텍스트 직접입력, 기술 없음) → jd_quality=weak, 배너 표시, 결과 흐림
[ ] 백엔드 공고 2종 → 분류 0.70+, regression 없음
```

- [ ] **Step 12.7: 최종 커밋**

```bash
cd "/Users/a0000/Library/Mobile Documents/com~apple~CloudDocs/Desktop/dev/nlp"
git add -A
git status  # 확인 후 커밋
git commit -m "feat: analysis quality redesign complete — RSC parsing, coverage metric, roadmap, UI"
```

---

## 빠른 참조

| 검증 명령 | 목적 |
|---|---|
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 전체 백엔드 테스트 |
| `PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py` | DB URL liveness |
| `PYTHONPATH=backend .venv/bin/python backend/tools/measure_coverage_baseline.py` | BASELINE/STRONG 측정 |
| `npm --prefix frontend run build` | TS 컴파일 |
| `npm --prefix frontend run e2e` | E2E 3종 |
| `curl http://127.0.0.1:8010/health` | health + resource_count |
