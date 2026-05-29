# 분석 품질 근본 재설계 — 설계 문서

**날짜**: 2026-05-30
**범위**: JD 추출 패러다임 전환 + 격차 점수 재설계 + 로드맵/리포트 재작성 + 추천DB 확장 + UI 개선
**전제**: 실측(잡코리아 공고 4건 fetch) 기반. 추정 아님.

---

## 0. 실측 근거 (이 설계의 토대)

`GI_Read/49244543`(원본 문제 공고) 외 살아있는 표준 공고 2건을 실제 `extract_url` + raw HTML로 분석한 결과:

| 공고 | RSC `skills`(HARD_SKILL) | `workFields`(직무명) | JSON-LD desc |
|------|--------------------------|----------------------|--------------|
| 데브툴즈 백엔드 | Node.js, NoSQL, Go, Restful API | 백엔드 개발자 | 95자(메타) |
| 한샘 백엔드 | JAVA, MSSQL, MySQL, Oracle, Spring Boot | 백엔드 개발자 | 85자(메타) |
| 와우바이오텍 AI | API, Node.js, Python, RPA, LLMOps, ChatGPT, AI Agent | AI 마케팅 자동화 엔지니어 | 94자(메타) |

**확정 사실:**
1. 잡코리아 GI_Read는 **Next.js**. 본문 데이터는 정적 HTML의 `<script>self.__next_f.push(...)</script>` RSC 페이로드에 JSON으로 인라인됨. 현재 `_VisibleTextParser`가 `<script>`를 버려서 **메타데이터(접수기간·복지·주소)만 추출** → 이것이 1·3·4·7번 문제의 단일 근본 원인.
2. 표준 공고는 `skills` 배열(`skillTypeCode:"HARD_SKILL"`)과 `workFields`(직무명)를 **일관되게** 제공. 태그는 **정밀(precision)이 높다**(실재하는 요구). 단 **재현율(recall)은 보장 못 함** — 광고주가 일부 기술을 누락(under-tag)할 수 있음. 그래서 본문 텍스트가 함께 있으면 보완 머지(아래 "텍스트 보완").
3. JSON-LD `JobPosting.description`은 85~95자 회사·위치 메타 요약 → **기술 본문 아님, 사용 안 함**.
4. 광고주 상세 본문(주요업무)은 **대부분 이미지** → 긴 텍스트 본문에 의존 불가.
5. `PageGbn=HH`(헤드헌팅/외부 등록) 공고는 RSC·JSON-LD·skills **전부 없음** → fallback + 경고 필수.
6. skills 명명이 제각각: `JAVA`, `Restful API`, `Go`, `NoSQL`, `MSSQL` → 정규화 필요.

**MLflow 오추출 경로 규명(BLOCK 1 답):** 49244543은 본문 텍스트가 안 잡혀 메타데이터만 입력됨 → 제목 "AI 마케팅 자동화 엔지니어"로 AI 분류 → AI taxonomy(MLflow 포함)를 메타 노이즈 문장과 sim 매칭 → MLflow가 evidence로 새어나옴. **skills 배열 직접 파싱이 이를 원천 차단.**

---

## 1. 영역 A — 잡코리아 JD 추출: RSC skills 배열 파싱

**파일**: `backend/app/services/text_extractor.py`

**새 데이터 구조** — `TextExtractionResult`에 선택 필드 추가:
```python
@dataclass(frozen=True)
class TextExtractionResult:
    text: str
    source_type: str
    extractor: str
    warnings: list[str]
    structured_skills: list[str] = field(default_factory=list)  # NEW: 공고 명시 기술 (정규화 전 원문)
    job_title: str | None = None                                 # NEW: workFields[0]
```

**로직** — `extract_url()` 내부, 잡코리아 도메인 분기:
```
extract_url(url):
  fetch HTML (기존 urlopen, User-Agent 유지)
  if host endswith "jobkorea.co.kr":
    payload = _decode_jobkorea_rsc(html)        # self.__next_f.push 청크 디코드
    skills  = _extract_jobkorea_skills(payload) # HARD_SKILL name 리스트
    title   = _extract_jobkorea_workfield(payload)
    body    = visible_text (메타 + 제목, 폴백/표시용)
    if skills:
      return TextExtractionResult(text=body 또는 재구성, source_type="url",
                                  extractor="jobkorea_rsc",
                                  structured_skills=skills, job_title=title, warnings=[])
    else:
      # HH/비표준 공고 → 경고
      warnings=["이 공고에서 구조화된 기술 정보를 찾지 못했습니다. 본문을 직접 붙여넣어 주세요."]
      return TextExtractionResult(text=body, ..., extractor="jobkorea_meta_only", warnings=warnings)
  else:
    기존 범용 파서 경로 (변경 없음)
```

**디코드 헬퍼**:
```python
def _decode_jobkorea_rsc(html: str) -> str:
    chunks = re.findall(r'self\.__next_f\.push\(\[\d+,("(?:[^"\\]|\\.)*")\]\)', html)
    out = []
    for c in chunks:
        try: out.append(json.loads(c))
        except Exception: pass
    return "".join(out)

def _extract_jobkorea_skills(payload: str) -> list[str]:
    pairs = re.findall(
        r'\{"name":"([^"]+)","rank":\d+,"manualInput":(?:true|false),"skillTypeCode":"HARD_SKILL"\}',
        payload,
    )
    # 순서 유지 중복 제거
    seen, result = set(), []
    for name in pairs:
        if name not in seen:
            seen.add(name); result.append(name)
    return result

def _extract_jobkorea_workfield(payload: str) -> str | None:
    m = re.search(r'"workFields":\["([^"]+)"', payload)
    return m.group(1) if m else None
```

**테스트**: 저장된 fixture HTML(3 공고)로 skills 추출 단위 테스트. 네트워크 의존 없음 — fixture를 `backend/tests/fixtures/jobkorea_*.html`로 커밋.

---

## 2. 영역 B — skills 명명 정규화

**파일**: `backend/app/services/c_part/skill_taxonomy.json` (aliases 확장) + `job_label_mapping.py` 또는 정규화 함수 재사용

실측에서 나온 변형 + 흔한 케이스 매핑 추가:
```json
"java": "Java", "JAVA": "Java",
"restful api": "REST API", "restful": "REST API", "rest": "REST API",
"mssql": "MSSQL", "ms-sql": "MSSQL",
"nodejs": "Node.js", "node": "Node.js",
"go": "Go", "golang": "Go",
"nosql": "NoSQL",
"chatgpt": "ChatGPT", "gpt": "ChatGPT",
"llmops": "LLMOps", "llm ops": "LLMOps",
"ai agent": "AI Agent", "rpa": "RPA", "langchain": "LangChain"
```
정규화는 기존 `normalize_skill_name()`(대소문자/alias) 재사용. 신규 스킬(Go, NoSQL, MSSQL, LLMOps, AI Agent, RPA, LangChain)은 taxonomy `skills`의 적절 직군에도 추가.

---

## 3. 영역 C — C파트: 명시 skills 직접 주입

**파일**: `backend/app/main.py` + `backend/app/services/c_part/pipeline.py`

**핵심 변경**: 잡코리아 `structured_skills`가 있으면 `extract_required_skills`(sim 추측)를 **우회**하고 그 목록을 required_skills로 사용.

```
/analyze 핸들러:
  job_extracted = extract (text/url)
  if job_extracted.structured_skills:
      norm = [normalize_skill_name(s) for s in structured_skills]   # 정규화
      analyzable = _filter_analyzable_skills(norm)                   # ↓ relevance 필터 (BLOCK 2)
      # 직무 분류 입력 보강 (BLOCK 1): 노이즈 메타 대신 직무명+기술 신호 강화
      classify_input = " ".join(filter(None, [job_extracted.job_title, *norm])) + "\n" + job_extracted.text
      c_result = run_c_part_analysis(..., explicit_required_skills=analyzable)
  else:
      classify_input = job_extracted.text
      c_result = run_c_part_analysis(...)  # 기존 sim 기반
  classification = classify_job(classify_input)
```

**BLOCK 1 — 직무 분류 입력 보강 (실측 확정)**: `classify_job`이 잡코리아 메타데이터 블롭으로 돌면 49244543이 AI 0.46 vs 데이터분석 0.40(차이 0.06, 불안정). `workFields`(직무명)+정규화 skills를 입력 앞에 붙이면 AI 신호(LLMOps·ChatGPT·AI Agent·Python)가 강해져 안정. **모델 재학습 아님 — 입력 텍스트 구성만 변경(D 역할 모델 불변).** 검증: 3 공고 재실행해 predicted_job 확인.

**BLOCK 2 — relevance 필터 (실측 확정)**: 49244543 배열에 `Notion·Slack·API`가 섞임 — 4주 로드맵 대상이 아님("Slack 학습 및 실습" 방지). `_filter_analyzable_skills`:
- **블랙리스트 제외**: 협업/일반 도구 `{Notion, Slack, Jira, Confluence, Figma(비FE문맥), API, Git, Excel}` 등 → 분석 대상에서 제외
- **화이트리스트 우선**: taxonomy `skills` 또는 추천DB에 매핑되는 기술만 gap 분석·로드맵 대상
- 매핑 안 되는 기술은 `required_skills`에 **표시는 하되**(공고 요구 투명성) gap/로드맵에선 제외
- `structured_skills` 전체는 응답에 별도 노출(공고가 요구한 전체 기술) — 분석 대상과 구분

`run_c_part_analysis`에 `explicit_required_skills: list[str] | None = None` 파라미터 추가:
- 주어지면 `extract_required_skills` 대신 그 목록을 required로 사용. **importance는 전부 "필수"로 간주** (잡코리아 skills 배열은 필수/우대를 구분하지 않으므로). → fit_score는 필수 그룹 평균 coverage로 계산됨.
- 각 required skill의 evidence는 "공고 명시 기술: {skill}" (노이즈 원문 없음 → 3·4·7 해결).
- 지원자 충족도(coverage)는 기존처럼 지원자 문장 sim으로 계산.

**텍스트 보완 머지 (사용자 선택 "skills 우선 + 텍스트 보완")**: skills 외에 본문 텍스트도 있으면(드묾 — 본문 대부분 이미지), 본문에서 taxonomy keyword_hit으로 추가 검출된 기술을 required에 **합집합**(under-tag 보완). 본문 없으면 skills만. → recall 보강.

> **정합성(advisor 지적)**: owned/partial/missing 분류와 fit_score가 **coverage 단일 소스**를 쓰도록 영역 D에서 통합.

---

## 4. 영역 D — gap_score → coverage 재설계 (단일 기준)

**파일**: `backend/app/services/c_part/pipeline.py` + `analyzer_rules.json`

**현재 문제**: `gap_score=(1-sim)*100`이 직관 불가. "충족"이 두 곳(gap loop의 `sim>=0.45`, 6.5 split)에서 따로 결정 → 불일치 위험.

**재설계 — coverage가 유일한 1차 지표**:
```
스킬별 best_sim = max(지원자 문장 vs 해당 스킬/요구) , 부정문 제외
coverage(0~100) = clamp((best_sim - BASELINE) / (STRONG - BASELINE), 0, 1) * 100
                  + (경험동사 있으면 +EXP_BONUS, 상한 100)
  BASELINE, STRONG, EXP_BONUS = 구현 시작 시 실제 sim 분포 측정 후 확정
  (초기값 후보 BASELINE≈0.25, STRONG≈0.55, EXP_BONUS≈15 — 측정으로 교체)
  ⚠️ SHARPEN(advisor): explicit-skills 모드의 coverage는 sim(맨 스킬 단어 "AI Agent" ↔ 지원자 문장)이
     주 경로다. 이 분포는 문장↔문장 sim과 다르므로, BASELINE/STRONG은 반드시
     "맨 스킬 단어 → 지원자 문장" 경로에서 측정해 보정한다.

gap_score = 100 - coverage   # 하위 호환 위해 필드 유지
```

**단일 분류 기준** (owned/partial/missing 모두 coverage로):
| coverage | 분류 |
|----------|------|
| ≥ 70 | owned (충족) |
| 40~69 | partial (보완 필요) |
| < 40 | missing (부족) |

**fit_score**도 coverage 평균 기반으로 통일 (필수 가중 70 / 우대 30 유지하되 그룹 점수 = 평균 coverage/100). 더 이상 matched_set/partial_set 이중 기준 없음.

**evidence 포맷**: `"공고 요구: {skill} / 내 자료 근거: '{문장 120자 이내}' (충족도 {coverage}%)"`. 근거 없으면 `"공고 요구: {skill} / 관련 경험 문장 미확인"`.

**테스트**: coverage 경계값(39/40/69/70) 분류 테스트, evidence 노이즈 없음 테스트.

---

## 5. 영역 E — 로드맵 재설계

**파일**: `backend/app/services/roadmap_generator.py`

**현재 버그**: `distribute_weeks` — 스킬 1개면 4주 모두 동일.

**재설계**:
```
대상 = 분석 가능(analyzable) 스킬 중 gap>0 만, gap 큰 순. 로드맵은 상위 N=min(스킬수, W, 5)개로 캡.
   (BLOCK 2 연계: Notion/Slack 등은 이미 analyzable에서 제외돼 로드맵에 안 들어옴)
N = 캡 적용 스킬 수, W = duration_weeks
if N >= W:  주차당 1스킬 (상위 W개)
if N <  W:  각 스킬에 연속 주차 배분 + 주차 내 단계(phase) 차등
  PHASES = ["기초 개념·환경", "핵심 기능 실습", "미니 프로젝트 적용", "정리·면접 대비"]
  스킬 1개/4주 → 4주 모두 같은 스킬이되 goal/practice가 PHASES[i]로 달라짐
  스킬 2개/4주 → 스킬A(1~2주 기초·실습), 스킬B(3~4주 기초·실습)
```
주차별 `goal`·`practice`·`recommended_titles`가 모두 달라지도록 보장. recommended_titles는 해당 스킬 추천자료에서 주차 단계에 맞는 것.

**테스트**: 스킬 1개/4주 → 4주 goal 전부 상이, 스킬 5개/4주 → 5개 중 4개 배분.

---

## 6. 영역 F — 리포트 재작성

**파일**: `backend/app/services/report_generator.py` (`generate_product_report`)

- evidence 원문 통째 삽입 **제거** (노이즈 차단)
- 구조: ① 직무·적합도 ② 요구 N개 중 충족 X·보완 Y·부족 Z ③ 최우선 보완 1~2개 + coverage% ④ 로드맵 요약(주차별 상이 반영)
- 빈/비표준 JD(경고)일 땐 적합도·격차 단정 표현 제거, 안내 문구로 대체

---

## 7. 영역 G — 추천 자료 DB 확장

**파일**: `backend/app/data/learning_resources.csv` + `backend/tools/audit_learning_resources.py`

실측 공고에 나왔으나 DB에 없는 주요 기술 우선 추가 (각 기술당 공식문서 + 유튜브 + 강의 2~4개, `reason` 필드 충실히):
- **AI/ML**: LLMOps, AI Agent, LangChain, ChatGPT/프롬프트엔지니어링, RAG, Vector DB
- **백엔드**: Go, NoSQL, Kafka(보강), gRPC
- **공통**: RPA, Notion/Slack 협업도구(간단)

확장 후 `audit_learning_resources.py`로 URL/스키마 검증. health `resource_count` 86 → 110+ 목표.

> skills 정규화 후에도 DB에 매칭 자료 없는 기술은 "추천자료 준비 중 — 공식문서 링크" 최소 1개 보장 또는 "해당 역량은 추천 자료가 아직 없습니다" 명시(거짓 추천 금지).

---

## 8. 영역 H — 빈/비표준 JD 경고 + 결과 suppress

**파일**: `backend/app/schemas.py` + `main.py` + `frontend/app/page.tsx`

- `AnalyzeResponse`에 `jd_quality: "ok" | "weak"` 필드 추가
- 판정: `structured_skills` 없고 required_skills < 3 → `"weak"`
- **advisor 지적 반영**: `weak`일 때 프론트는 fit_score·gap 차트·로드맵을 **흐리게 처리 + 상단 경고 배너** ("이 공고에서 명확한 기술 요구를 찾지 못했습니다. 개발 직무 공고인지 확인하거나 본문을 직접 붙여넣어 주세요."). "77점 적합 + 기술 요구 없음" 자기모순 제거.

---

## 9. 영역 I — 프론트 UI 개선

**파일**: `frontend/app/page.tsx` + `frontend/app/globals.css` + `frontend/lib/types.ts`

- **역량 격차 차트**: 단방향 막대 → **충족 X% / 부족 Y% 양방향 + 컬러존**(green 70+/amber 40-69/red <40), 축 라벨 "충족도".
- **추천 자료 카드**: `resource.reason` 표시("왜 추천?"), recommend_score 근거(난이도·신뢰도) 미니 표시, type/시간/무료 배지, hover 개선.
- **충족/부족/보완 분류** 카드에 coverage% 노출.
- 경고 배너 컴포넌트(영역 H).
- 타입 동기화: `AnalyzeResponse`에 `jd_quality`, skill 항목에 `coverage` 반영.

---

## 검증 계획

```bash
# 백엔드 (기존 46 + 신규: skills파싱/coverage경계/로드맵비반복/경고)
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
# DB 검증
PYTHONPATH=backend .venv/bin/python backend/tools/audit_learning_resources.py
# 프론트
npm --prefix frontend run build
npm --prefix frontend run e2e
# 실제 동작 (근본 검증): 49244543 URL + 백엔드/AI 공고 + 비개발 공고 3종
#   → 브라우저에서 required_skills 정확/evidence 깨끗/로드맵 상이/경고 동작 눈으로 확인
```

**성공 기준**:
1. 49244543 → 공고 요구 기술(표시) = 정규화된 skills 전체; **분석·로드맵 대상** = Python·LLMOps·ChatGPT·AI Agent·RPA 등(Notion·Slack·API 제외); MLflow 등 taxonomy 억지 추출 0; predicted_job = AI/ML(분류 입력 보강 후 안정)
2. evidence·report에 "접수기간/복지/주소" 노이즈 문장 0
3. 4주 로드맵 goal 4개 상이
4. 추천 카드에 추천 이유 표시
5. 비표준/비개발 공고 → 경고 배너 + 결과 흐림

---

## 작업 순서 (의존성)

```
A(추출) → B(정규화) → C(주입) → D(coverage) → E(로드맵) → F(리포트)
G(DB확장)  ── 독립, C와 병행 가능
H(경고) → I(UI)  ── D 이후
```

## 미적용 (범위 외)
- 잡코리아 외 사이트(사람인/원티드) 전용 파서 — 범용 파서로 폴백
- 상세 본문 이미지 OCR (별개 기능, 이미 PDF OCR은 구현됨)
- 직무 분류기 재학습 (workFields를 분류 보조로만 활용, 모델 재학습은 B 역할)
