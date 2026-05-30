"""
[C파트 - v7]
Ko-Sentence-RoBERTa 기반 직무 역량 격차 분석 모듈

변경 이력:
  v1  초기 구현 (target_job_skills 외부 주입, 전체 벡터 비교)
  v2  D파트 JSON 규격 맞춤, 부정 표현 감지, 문장 단위 비교, Lazy Load
  v3  JD 요구 역량 자동 추출, 지원자 보유 역량 자동 추출,
      keyword_hit 단독 충족 제거, gap_score 하한선, fit_score 재설계
  v4  skill_taxonomy.json / analyzer_rules.json 외부 파일 연동,
      오류 응답 규격 추가, 입력 어댑터 추가 (텍스트 / txt / PDF)
  v5  load_text() 긴 문자열 "File name too long" 버그 수정,
      fit_score 구조적 버그 수정 (없는 그룹 1.0 만점 처리 제거),
      owned / partial / gap 3분류 체계 도입,
      taxonomy coverage 보강 (Kubernetes, Spring Security 등),
      b_predicted_job 입력 주의사항 docstring 명시
  v6  partial_skills가 skill_gaps에 동시 포함되는 중복 버그 수정
      → partial로 분류된 스킬을 skill_gaps에서 명시적 제거
  v7  도큐스트링 버전 표기 동기화,
      extract_required_skills keyword_hit 갱신 누락 버그 수정,
      extract_owned_skills 경험 동사 없는 단순 언급 partial 분류 방지,
      fit_score에 partial_skills 부분 반영 (가중치 0.5),
      스킬/JD 문장 임베딩 중복 계산 제거 (skill_vec 캐시),
      b_predicted_job 오류 메시지 개선

실행 방법:
  pip install transformers torch numpy pypdf2
  python c_part_pipeline.py

모델 캐시 위치:
  Linux/Mac : ~/.cache/huggingface/hub/
  Windows   : C:\\Users\\<user>\\.cache\\huggingface\\hub\\
"""

import re
import json
import numpy as np
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────
# 1. 외부 설정 파일 로드
# ─────────────────────────────────────────────────────────────────────

_BASE_DIR = Path(__file__).parent

def _load_json(filename: str) -> dict:
    path = _BASE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"[C파트] 설정 파일 없음: {path}\n"
            f"c_part_pipeline.py 와 같은 폴더에 {filename} 이 있어야 합니다."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)

_TAXONOMY = _load_json("skill_taxonomy.json")
_RULES    = _load_json("analyzer_rules.json")

# ── 설정값 추출 ───────────────────────────────────────────────────────
JOB_GROUP_MAPPING  = _TAXONOMY["job_group_mapping"]
SKILL_DB           = _TAXONOMY["skills"]           # {"backend": [...], ...}
SKILL_ALIASES      = _TAXONOMY["aliases"]

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
        pattern = rf'(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])'
        return bool(re.search(pattern, text, re.IGNORECASE))

    if _hit(skill, sentence):
        return True
    for alias in _REVERSE_ALIASES.get(skill, set()):
        if _hit(alias, sentence):
            return True
    return False


REQUIRED_KEYWORDS  = _RULES["importance"]["required_keywords"]
PREFERRED_KEYWORDS = _RULES["importance"]["preferred_keywords"]
DEFAULT_IMPORTANCE = _RULES["importance"]["default"]

NEGATION_PATTERNS       = _RULES["negation_patterns"]
EXPERIENCE_VERB_PATTERNS= _RULES["experience_verb_patterns"]

THR_SKILL_MATCH   = _RULES["thresholds"]["skill_match"]
THR_JD_EXTRACT    = _RULES["thresholds"]["jd_extract"]
THR_CAND_ANCHOR   = _RULES["thresholds"]["candidate_anchor"]
THR_OWNED_SKILL   = _RULES["thresholds"]["owned_skill"]
EXP_VERB_PENALTY  = _RULES["thresholds"]["experience_verb_penalty"]

GAP_FLOOR         = _RULES["gap_score"]["floor"]          # {"필수": 85, "우대": 65}
GAP_LEVEL_HIGH    = _RULES["gap_score"]["levels"]["high"]
GAP_LEVEL_MEDIUM  = _RULES["gap_score"]["levels"]["medium"]

FIT_W_REQUIRED    = _RULES["fit_score"]["required_weight"]
FIT_W_PREFERRED   = _RULES["fit_score"]["preferred_weight"]

# ── coverage 재설계 상수 (Task 3 실측값) ─────────────────────────────
COV_BASELINE   = 0.241   # 이 이하 sim → coverage 0
COV_STRONG     = 0.435   # 이 이상 sim → coverage 100
COV_EXP_BONUS  = 15.0    # 경험 동사 있을 때 coverage 보너스
COV_OWNED_THR  = 70      # coverage >= 이 값 → owned
COV_PARTIAL_LO = 40      # 40 <= coverage < 70 → partial
                         # coverage < 40 → missing

# ── relevance 필터 상수 ───────────────────────────────────────────────
_WHITELIST_SKILLS: set[str] = {
    s.lower()
    for group in _TAXONOMY.get("skills", {}).values()
    for s in group
}

_BLACKLIST_SKILLS: set[str] = {
    "notion", "slack", "jira", "confluence", "figma",
    "api", "git", "github", "gitlab", "excel", "powerpoint",
    "google docs", "google sheets", "teams", "zoom",
}


def _filter_analyzable_skills(skills: list[str]) -> list[str]:
    """
    1. 블랙리스트 제외 (협업/일반 도구)
    2. 화이트리스트(taxonomy skills 배열)에 있는 기술만 포함
    화이트리스트 미매핑 기술은 제외 (structured_skills에는 별도 표시)
    """
    result = []
    for s in skills:
        if s.lower() in _BLACKLIST_SKILLS:
            continue
        if s.lower() in _WHITELIST_SKILLS:
            result.append(s)
    return result

MODEL_NAME = "jhgan/ko-sroberta-multitask"

# ─────────────────────────────────────────────────────────────────────
# 2. 모델 Lazy Load
# ─────────────────────────────────────────────────────────────────────

_tokenizer = None
_model     = None

def _load_model():
    """최초 호출 시점에만 모델 로드 후 캐시 반환."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            print(f"[C파트] 모델 로딩 중: {MODEL_NAME}")
            print("[C파트] 최초 실행 시 모델 자동 다운로드 (~400MB)")
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            _model     = AutoModel.from_pretrained(MODEL_NAME)
            _model.eval()
            print("[C파트] 모델 로딩 완료")
        except Exception as e:
            raise RuntimeError(
                f"[C파트] 모델 로딩 실패: {e}\n"
                "해결: pip install transformers torch\n"
                f"캐시 위치: ~/.cache/huggingface/hub/"
            )
    return _tokenizer, _model


# ─────────────────────────────────────────────────────────────────────
# 3. 임베딩 & 유사도
# ─────────────────────────────────────────────────────────────────────

def get_embedding(text: str) -> np.ndarray:
    """Mean Pooling 기반 문장 임베딩."""
    import torch
    tokenizer, model = _load_model()
    inputs = tokenizer(text, padding=True, truncation=True,
                       return_tensors="pt", max_length=256)
    with torch.no_grad():
        outputs = model(**inputs)
    emb  = outputs[0]
    mask = inputs["attention_mask"].unsqueeze(-1).expand(emb.size()).float()
    return (torch.sum(emb * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)).numpy()[0]


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.clip(np.dot(a, b) / denom, 0.0, 1.0)) if denom else 0.0


# ─────────────────────────────────────────────────────────────────────
# 4. 텍스트 전처리 유틸
# ─────────────────────────────────────────────────────────────────────

def split_sentences(text: str) -> list[str]:
    """줄바꿈 + 마침표/느낌표/물음표 기준 문장 분리."""
    sentences = []
    for line in re.split(r"\n+", text.strip()):
        for part in re.split(r"(?<=[.!?])\s+", line.strip()):
            part = part.strip()
            if len(part) > 5:
                sentences.append(part)
    return sentences or [text.strip()]


def has_negation(sentence: str) -> bool:
    return any(re.search(p, sentence) for p in NEGATION_PATTERNS)


def has_experience_verb(sentence: str) -> bool:
    return any(re.search(p, sentence) for p in EXPERIENCE_VERB_PATTERNS)


def extract_importance(jd_sentence: str) -> str:
    lower = jd_sentence.lower()
    for kw in PREFERRED_KEYWORDS:
        if kw in lower:
            return "우대"
    for kw in REQUIRED_KEYWORDS:
        if kw in lower:
            return "필수"
    return DEFAULT_IMPORTANCE


def normalize_skill_name(skill: str) -> str:
    """aliases 테이블 기준으로 스킬명 정규화."""
    return SKILL_ALIASES.get(skill, SKILL_ALIASES.get(skill.lower(), skill))


def _gap_level(gap_score: int) -> str:
    if gap_score >= GAP_LEVEL_HIGH:
        return "높음"
    elif gap_score >= GAP_LEVEL_MEDIUM:
        return "중간"
    return "낮음"


def _compute_coverage(best_sim: float, has_exp_verb: bool = False) -> float:
    """코사인 유사도 → coverage(0~100) 변환."""
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


# ─────────────────────────────────────────────────────────────────────
# 5. 입력 어댑터 (텍스트 / .txt 파일 / PDF)
# ─────────────────────────────────────────────────────────────────────

def load_text(source: str) -> str:
    """
    세 가지 입력을 모두 str로 반환.
      - 일반 문자열     → 그대로 반환
      - .txt 파일 경로  → 파일 읽기
      - .pdf 파일 경로  → PyPDF2로 텍스트 추출

    [v5 수정] 긴 문자열을 Path()에 넘기면 OS에서 "File name too long" 오류가 발생하는
    버그를 수정. Path() 시도 전에 "파일 경로일 가능성"을 먼저 검사한다.
      - 줄바꿈 포함  → 원문 텍스트로 즉시 처리
      - 255자 초과   → 원문 텍스트로 즉시 처리
      - 위 조건 모두 통과한 경우에만 Path() 로 파일 존재 여부 확인
    """
    # 줄바꿈이 있거나 255자를 초과하면 파일 경로가 아닌 텍스트 원문으로 판단
    if "\n" in source or len(source) > 255:
        return source

    # 파일 경로 시도 (OS 예외를 추가로 방어)
    try:
        path = Path(source)
        if path.exists():
            if path.suffix.lower() == ".pdf":
                try:
                    import PyPDF2
                    text = []
                    with open(path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            extracted = page.extract_text()
                            if extracted:
                                text.append(extracted)
                    result = "\n".join(text).strip()
                    if not result:
                        raise ValueError(
                            "PDF에서 텍스트를 추출하지 못했습니다 (스캔 PDF일 수 있음)."
                        )
                    return result
                except ImportError:
                    raise ImportError(
                        "PDF 읽기에 PyPDF2가 필요합니다.\n"
                        "설치: pip install PyPDF2"
                    )
            else:
                # .txt 또는 기타 텍스트 파일
                return path.read_text(encoding="utf-8")
    except (OSError, ValueError):
        # 경로 길이 제한 등 OS 예외 → 텍스트 원문으로 폴백
        pass

    # 파일이 없거나 경로가 아닌 짧은 문자열 → 원문 그대로 반환
    return source


# ─────────────────────────────────────────────────────────────────────
# 6. JD 요구 역량 자동 추출
# ─────────────────────────────────────────────────────────────────────

def extract_required_skills(
    job_key: str,
    jd_sentences: list[str],
    jd_vectors: list[np.ndarray],
) -> list[dict]:
    """
    skill_taxonomy.json의 직무별 스킬 목록을 앵커로 사용해
    JD 원문에서 요구 역량을 자동 추출.

    Returns:
        [{"skill": str, "importance": str, "source_sentence": str}, ...]
    """
    taxonomy   = SKILL_DB.get(job_key, [])
    if not taxonomy:
        all_skills = [s for lst in SKILL_DB.values() for s in lst]
        taxonomy   = list(dict.fromkeys(all_skills))  # 중복 제거 순서 유지

    required: list[dict] = []
    seen: set[str]       = set()

    for raw_skill in taxonomy:
        skill     = normalize_skill_name(raw_skill)
        skill_vec = get_embedding(skill)

        best_sentence = None
        best_sim_val  = 0.0

        for sentence, vec in zip(jd_sentences, jd_vectors):
            sim         = cosine_sim(vec, skill_vec)
            keyword_hit = _keyword_hit_any(skill, sentence)
            if keyword_hit or sim >= THR_JD_EXTRACT:
                # [v7 수정] keyword_hit이면 유사도가 낮아도 갱신 보장.
                # 키워드가 직접 등장한 문장이 가장 신뢰도 높은 근거이므로
                # 비교 기준값을 1.0으로 올려 항상 채택되도록 처리.
                effective_sim = 1.0 if keyword_hit else sim
                if effective_sim > best_sim_val:
                    best_sim_val  = effective_sim
                    best_sentence = sentence

        if best_sentence and skill not in seen:
            seen.add(skill)
            required.append({
                "skill":           skill,
                "importance":      extract_importance(best_sentence),
                "source_sentence": best_sentence,
                "_skill_vec":      skill_vec,   # [v7] 6단계 중복 임베딩 방지용 캐시
            })

    return required


# ─────────────────────────────────────────────────────────────────────
# 7. 지원자 보유 역량 자동 추출
# ─────────────────────────────────────────────────────────────────────

def extract_owned_skills(
    candidate_sentences: list[str],
    candidate_vectors: list[np.ndarray],
    required_skills: list[dict],
) -> list[dict]:
    """
    required_skills 기준으로 지원자 문장을 탐색해 보유 역량 추출.
    부정 표현 포함 문장은 제외.
    경험 동사 있으면 evidence_strength = "direct", 없으면 "contextual".

    Returns:
        [{"skill": str, "evidence": str, "evidence_strength": str}, ...]
    """
    owned: list[dict] = []
    seen: set[str]    = set()

    for req in required_skills:
        skill     = req["skill"]
        skill_vec = get_embedding(skill)

        best_sentence = None
        best_sim_val  = 0.0
        best_strength = "contextual"

        for sentence, vec in zip(candidate_sentences, candidate_vectors):
            if has_negation(sentence):
                continue

            sim         = cosine_sim(vec, skill_vec)
            keyword_hit = _keyword_hit_any(skill, sentence)
            has_exp_v   = has_experience_verb(sentence)

            # [v7 수정] keyword_hit만 있고 경험 동사가 없는 단순 언급은 후보에서 제외.
            # "Docker는 들어본 적 있음"처럼 키워드가 있어도 경험 근거가 없으면
            # partial_skills에도 올라가지 않도록 막는다.
            # 유사도 기반 후보(contextual)는 그대로 허용.
            if keyword_hit and not has_exp_v:
                continue

            if keyword_hit or sim >= THR_OWNED_SKILL:
                strength  = "direct" if (keyword_hit and has_exp_v) else "contextual"
                is_better = (
                    (strength == "direct" and best_strength != "direct") or
                    (strength == best_strength and sim > best_sim_val)
                )
                if is_better:
                    best_sentence = sentence
                    best_sim_val  = sim
                    best_strength = strength

        if best_sentence and skill not in seen:
            seen.add(skill)
            owned.append({
                "skill":             skill,
                "evidence":          best_sentence,
                "evidence_strength": best_strength,
            })

    return owned


# ─────────────────────────────────────────────────────────────────────
# 8. gap_score & evidence 계산
# ─────────────────────────────────────────────────────────────────────

def _compute_gap(
    jd_sentence: str,
    best_candidate: Optional[tuple[str, float]],
    importance: str,
) -> tuple[int, str]:
    """
    gap_score (0~100, 높을수록 부족) 와 evidence 문자열 반환.
    증거 없으면 importance 기준 하한선 강제 적용.
    """
    floor = GAP_FLOOR.get(importance, 65)

    if best_candidate is None:
        return floor, (
            f"JD 요구사항: '{jd_sentence}' / "
            f"지원자 자료에서 해당 역량의 경험 문장이 확인되지 않거나 "
            f"부정적 맥락으로만 등장함"
        )

    cand_sentence, cand_sim = best_candidate
    gap_score = max(round((1.0 - cand_sim) * 100), 0)
    evidence  = (
        f"JD 요구사항: '{jd_sentence}' / "
        f"지원자 관련 문장: '{cand_sentence}' — "
        f"언급은 있으나 충분한 경험 근거 미확인 (유사도 {cand_sim*100:.1f}%)"
    )
    return gap_score, evidence


# ─────────────────────────────────────────────────────────────────────
# 9. fit_score (역량 충족률 기반)
# ─────────────────────────────────────────────────────────────────────

def _compute_fit_score(
    required_skills: list[str],
    skill_coverage_map: dict[str, float],
    importance_map: dict[str, str],
) -> int:
    """
    fit_score = 필수그룹 평균coverage × 0.7 + 우대그룹 평균coverage × 0.3
    없는 그룹은 존재하는 그룹으로만 재배분.
    """
    required_covs  = [skill_coverage_map.get(s, 0.0) for s in required_skills if importance_map.get(s) == "필수"]
    preferred_covs = [skill_coverage_map.get(s, 0.0) for s in required_skills if importance_map.get(s) == "우대"]

    if required_covs and preferred_covs:
        score = (float(np.mean(required_covs)) * (FIT_W_REQUIRED / 100.0)
                 + float(np.mean(preferred_covs)) * (FIT_W_PREFERRED / 100.0))
    elif required_covs:
        score = float(np.mean(required_covs))
    elif preferred_covs:
        score = float(np.mean(preferred_covs))
    else:
        score = 0.0

    return int(round(max(0.0, min(100.0, score))))


# ─────────────────────────────────────────────────────────────────────
# 10. C파트 마스터 분석 엔진
# ─────────────────────────────────────────────────────────────────────

def run_c_part_analysis(
    b_predicted_job: str,
    jd_input: str,
    candidate_input: str,
    threshold: float = THR_SKILL_MATCH,  # kept for backward compat; no longer used for classification (coverage-based)
    *,
    explicit_required_skills: list[str] | None = None,  # NEW: from RSC skills array
) -> dict:
    """
    B파트 직무 라벨 + JD + 지원자 서류 → D파트 표준 입력 JSON 자동 생성.

    Parameters:
        b_predicted_job : B파트 predict()가 반환하는 영문 직무 라벨.
                          반드시 classification.job_label 값을 사용할 것.
                          ("backend" / "frontend" / "data_analyst" / "ai")
                          ※ 한국어 직무명("백엔드 개발자" 등)을 넣으면 오류 반환.
        jd_input        : 채용공고 원문 텍스트, .txt 경로, 또는 .pdf 경로
        candidate_input : 지원자 서류 원문 텍스트, .txt 경로, 또는 .pdf 경로
        threshold       : 충족 판정 코사인 유사도 기준 (기본값 analyzer_rules.json)

    Returns:
        성공 시 → result["status"] == "success" 확인 후 D파트에 전달할 것.
        {
            "status":          "success",
            "predicted_job":   str,
            "fit_score":       int,
            "required_skills": [...],
            "owned_skills":    [...],    # 충족 판정 스킬 근거
            "partial_skills":  [...],    # 근거 있으나 임계값 미달 스킬
            "matched_skills":  [...],
            "skill_gaps":      [...],
            "_meta":           {...}
        }
        실패 시 → D파트에 직접 전달하지 말 것. status 확인 후 로그 처리.
        {
            "status":  "error",
            "message": str
        }
    """
    try:
        # ── 0. 입력 어댑터 ────────────────────────────────────────────
        jd_text        = load_text(jd_input)
        candidate_text = load_text(candidate_input)

        if not jd_text.strip():
            raise ValueError("JD 텍스트가 비어 있습니다.")
        if not candidate_text.strip():
            raise ValueError("지원자 서류 텍스트가 비어 있습니다.")

        # ── 1. B파트 라벨 동기화 ─────────────────────────────────────
        job_key         = b_predicted_job.strip().lower()
        korean_job_name = JOB_GROUP_MAPPING.get(job_key)
        if not korean_job_name:
            # [v7] 한국어 직무명이 들어온 경우 역방향 힌트 제공
            reverse_map = {v: k for k, v in JOB_GROUP_MAPPING.items()}
            hint = ""
            if b_predicted_job in reverse_map:
                hint = (
                    f" 힌트: '{b_predicted_job}'은 한국어 직무명입니다. "
                    f"B파트 predict()의 'predicted_job' 필드(영문 라벨) "
                    f"'{reverse_map[b_predicted_job]}'을 사용하세요."
                )
            raise ValueError(
                f"B파트 라벨 '{b_predicted_job}'은 정의되지 않은 값입니다. "
                f"허용값: {list(JOB_GROUP_MAPPING.keys())}{hint}"
            )

        # ── 2. 문장 분리 ─────────────────────────────────────────────
        jd_sentences        = split_sentences(jd_text)
        candidate_sentences = split_sentences(candidate_text)

        # ── 3. 임베딩 사전 계산 ──────────────────────────────────────
        print(f"[C파트] JD 문장 {len(jd_sentences)}개 임베딩 중...")
        jd_vectors = [get_embedding(s) for s in jd_sentences]

        print(f"[C파트] 지원자 문장 {len(candidate_sentences)}개 임베딩 중...")
        candidate_vectors = [get_embedding(s) for s in candidate_sentences]

        # ── 4. JD 요구 역량 결정 ────────────────────────────────────
        if explicit_required_skills is not None:
            print(f"[C파트] 명시 스킬 {len(explicit_required_skills)}개 사용 (RSC 직접 주입)")
            # explicit 모드: 스킬명을 직접 embed해 skill_vec 생성
            # importance = 모두 "필수" (잡코리아 skills 배열은 필수/우대 미구분)
            explicit_vecs = [get_embedding(s) for s in explicit_required_skills]
            required_skills = [
                {
                    "skill":          s,
                    "importance":     "필수",
                    "source_sentence": s,  # 스킬명 자체가 source
                    "_skill_vec":     v,
                }
                for s, v in zip(explicit_required_skills, explicit_vecs)
            ]
        else:
            print("[C파트] JD 요구 역량 추출 중...")
            required_skills = extract_required_skills(job_key, jd_sentences, jd_vectors)
            print(f"[C파트] 요구 역량 {len(required_skills)}개 추출")

        # ── 5. 지원자 보유 역량 후보 탐색 (내부용) ──────────────────────
        # [v5] extract_owned_skills()는 후보 맵 구성용으로만 사용.
        # 최종 owned_skills / partial_skills는 6단계 판정 후 재구성한다.
        print("[C파트] 지원자 보유 역량 추출 중...")
        _owned_candidates = extract_owned_skills(candidate_sentences, candidate_vectors, required_skills)
        _owned_map        = {s["skill"]: s for s in _owned_candidates}

        # ── 6. 스킬별 격차 분석 ──────────────────────────────────────
        matched_skills: list[str] = []
        skill_gaps: list[dict]    = []
        skill_coverage_map: dict[str, float] = {}
        importance_map_local: dict[str, str] = {}

        # explicit 모드에서는 의미적 오탐 방지를 위해 candidate pool 임계값을 높임.
        # (THR_CAND_ANCHOR=0.3은 text 모드용 — explicit 모드에서는 "자동화" 문장이
        # RPA의 best evidence로 선택되는 false positive가 발생)
        _cand_pool_threshold = 0.50 if explicit_required_skills is not None else THR_CAND_ANCHOR

        # [v7] JD 요구 문장 벡터 사전 캐시 (source_sentence → vec)
        # source_sentence가 jd_sentences에 있으면 이미 계산된 벡터 재사용
        jd_sent_vec_map = dict(zip(jd_sentences, jd_vectors))

        for req in required_skills:
            skill       = req["skill"]
            importance  = req["importance"]
            source_sent = req["source_sentence"]

            # [v7] extract_required_skills에서 계산한 skill_vec 재사용
            skill_vec = req.get("_skill_vec")
            if skill_vec is None:
                skill_vec = get_embedding(skill)
            # [v7] JD 요구 문장 벡터도 캐시에서 먼저 조회
            jd_req_vec = jd_sent_vec_map.get(source_sent)
            if jd_req_vec is None:
                jd_req_vec = get_embedding(source_sent)

            best_sentence    = None
            best_sim_val     = 0.0
            any_keyword_hit  = False  # 후보 텍스트에 스킬 키워드가 실제로 등장했는지

            for sentence, cand_vec in zip(candidate_sentences, candidate_vectors):
                if has_negation(sentence):
                    continue

                # skill 벡터 ↔ 지원자 문장 비교
                # jd_cand_sim (JD 요구 문장 ↔ 지원자 문장)은 같은 도메인 텍스트에서
                # false positive를 유발함 — "AI 기술 학습 중"이 Python/MLOps/Docker에
                # 모두 매칭되는 버그 원인. skill_sim만 사용.
                skill_sim   = cosine_sim(skill_vec,  cand_vec)
                sim         = skill_sim

                keyword_hit = _keyword_hit_any(skill, sentence)
                has_exp_v   = has_experience_verb(sentence)

                if keyword_hit:
                    any_keyword_hit = True

                if keyword_hit or sim >= _cand_pool_threshold:
                    # 경험 동사 없는 단순 키워드 등장 → 유사도 감쇄
                    if keyword_hit and not has_exp_v:
                        sim *= EXP_VERB_PENALTY

                    if sim > best_sim_val:
                        best_sim_val  = sim
                        best_sentence = sentence

            # ── coverage 계산 + 분류 ────────────────────────────────────
            # 핵심 규칙: 후보 텍스트에 스킬 키워드가 없으면 owned/partial 불가 → missing.
            # 의미적 유사도만으로는 "보유"를 주장할 수 없다. 거짓말 금지.
            if not any_keyword_hit:
                best_sim_val  = 0.0
                best_sentence = None

            best_has_exp = has_experience_verb(best_sentence) if best_sentence else False
            coverage = _compute_coverage(best_sim_val, has_exp_verb=best_has_exp)
            skill_coverage_map[skill] = coverage
            importance_map_local[skill] = importance

            cat, _ = _coverage_level(coverage)
            gap_score = max(round(100.0 - coverage), 0)  # backward compat
            gap_level = _gap_level(gap_score)

            if cat == "owned":
                matched_skills.append(skill)
            else:
                # evidence 포맷 (기존 _compute_gap 대체)
                if best_sentence:
                    evidence = (
                        f"공고 요구: {skill} / "
                        f"내 자료 근거: '{best_sentence[:120]}' "
                        f"(충족도 {coverage:.0f}%)"
                    )
                else:
                    evidence = f"공고 요구: {skill} / 관련 경험 문장 미확인"
                skill_gaps.append({
                    "skill":      skill,
                    "gap_score":  gap_score,
                    "gap_level":  gap_level,
                    "importance": importance,
                    "evidence":   evidence,
                    "coverage":   coverage,
                })

        # ── 6.5 coverage 기반 owned / partial / missing 분리 ─────────
        owned_skills:   list[dict] = []
        partial_skills: list[dict] = []

        # owned: matched_skills (coverage >= 70)
        for skill in matched_skills:
            coverage = skill_coverage_map.get(skill, 100.0)
            entry = _owned_map.get(
                skill, {"skill": skill, "evidence": "", "evidence_strength": "contextual"}
            )
            # skill_coverage_map에서 coverage 추가 (owned이므로 반드시 >=70)
            owned_skills.append({**entry, "coverage": coverage})

        # partial/missing: skill_gaps에서 coverage로 분리
        remaining_gaps = []
        for gap in skill_gaps:
            skill = gap["skill"]
            coverage = gap["coverage"]
            cat, _ = _coverage_level(coverage)

            if cat == "partial":
                cand = _owned_map.get(skill)
                partial_skills.append({
                    "skill":             skill,
                    "evidence":          cand["evidence"] if cand else gap["evidence"],
                    "evidence_strength": cand["evidence_strength"] if cand else "weak",
                    "gap_score":         gap["gap_score"],
                    "gap_level":         gap["gap_level"],
                    "importance":        gap["importance"],
                    "note":              f"충족도 {coverage:.0f}% — 보완 필요",
                    "coverage":          coverage,
                })
            else:  # missing (coverage < 40)
                remaining_gaps.append({**gap})

        skill_gaps = remaining_gaps

        # ── 7. fit_score 산출 ─────────────────────────────────────────
        fit_score = _compute_fit_score(
            required_skills=[req["skill"] for req in required_skills],
            skill_coverage_map=skill_coverage_map,
            importance_map=importance_map_local,
        )

        # ── 8. 출력 JSON 빌드 ─────────────────────────────────────────
        return {
            "status":          "success",
            "predicted_job":   korean_job_name,
            "fit_score":       fit_score,
            "required_skills": [
                {k: v for k, v in s.items() if k != "_skill_vec"}
                for s in required_skills
            ],
            "owned_skills":    owned_skills,
            "partial_skills":  partial_skills,
            "matched_skills":  matched_skills,
            "skill_gaps":      skill_gaps,
            "_meta": {
                "b_part_raw_label":         b_predicted_job,
                "jd_sentence_count":        len(jd_sentences),
                "candidate_sentence_count": len(candidate_sentences),
                "taxonomy_source":          "skill_taxonomy.json",
                "rules_source":             "analyzer_rules.json",
                "taxonomy_note": (
                    "직무별 역량 taxonomy 기반 분석 "
                    "(JD 완전 자동 추출이 아닌 taxonomy-JD 매칭 방식)"
                ),
            },
        }

    except Exception as e:
        return {
            "status":  "error",
            "message": str(e),
        }


# ─────────────────────────────────────────────────────────────────────
# 🧪 로컬 검증 시나리오
# ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== [C파트 v4] 로컬 검증 ===\n")
    print("실행 전 필수: pip install transformers torch numpy\n")

    sample_jd = (
        "저희 팀은 Java와 Spring Boot 기반의 백엔드 개발 경험이 있는 분을 모십니다.\n"
        "Docker 및 Kubernetes를 활용한 컨테이너 운영 경험이 필수입니다.\n"
        "AWS 환경에서의 배포 및 운영 경험이 있으면 우대합니다.\n"
        "REST API 설계 및 구현 역량이 필수적으로 요구됩니다.\n"
        "CI/CD 파이프라인 구성 경험이 있으신 분을 우대합니다."
    )
    sample_candidate = (
        "Spring Boot를 이용해 게시판 CRUD API를 직접 개발하고 배포해 본 경험이 있습니다.\n"
        "REST API 설계 원칙에 따라 팀 프로젝트에서 API를 직접 설계하고 구현했습니다.\n"
        "Docker는 들어본 적 있지만 실무에서 사용해 본 경험은 없습니다.\n"
        "AWS는 EC2를 간단히 사용해 본 정도이며 운영 경험은 부족합니다.\n"
        "Kubernetes나 CI/CD 도구는 아직 공부한 적이 없습니다."
    )

    result = run_c_part_analysis(
        b_predicted_job="backend",
        jd_input=sample_jd,
        candidate_input=sample_candidate,
    )

    print("\n=== 출력 JSON ===")
    print(json.dumps(result, indent=4, ensure_ascii=False))

    if result["status"] == "success":
        print("\n=== 검증 ===")

        # 검증 1: Docker keyword 단독 충족 방지
        docker_in_gaps    = any(g["skill"] == "Docker" for g in result["skill_gaps"])
        docker_in_matched = "Docker" in result["matched_skills"]
        if docker_in_gaps:
            print("✅ Docker → skill_gaps (keyword 단독 충족 방지 정상)")
        elif docker_in_matched:
            print("❌ Docker → matched_skills (버그: '들어본 적 있음'이 충족 처리됨)")

        # 검증 2: 증거 없는 필수 역량 gap_score 하한선
        for gap in result["skill_gaps"]:
            if gap["importance"] == "필수":
                floor = GAP_FLOOR["필수"]
                status = "✅" if gap["gap_score"] >= floor else "❌"
                print(f"{status} {gap['skill']} gap_score={gap['gap_score']} "
                      f"(필수 하한선 {floor} {'이상' if gap['gap_score'] >= floor else '미만'})")
                break

        # 검증 3: fit_score 구성 확인
        print(f"\nfit_score={result['fit_score']} "
              f"(matched={len(result['matched_skills'])} / "
              f"required={len(result['required_skills'])})")

        # 검증 4: owned / partial / gap 완전 분리 확인
        owned_set   = {s["skill"] for s in result["owned_skills"]}
        partial_set = {s["skill"] for s in result["partial_skills"]}
        gap_set     = {g["skill"] for g in result["skill_gaps"]}
        overlap_op  = owned_set & partial_set
        overlap_og  = owned_set & gap_set
        overlap_pg  = partial_set & gap_set   # ← v6 핵심 검사
        print("\n=== [검증 4] owned / partial / gap 완전 분리 검사 ===")
        print(f"owned_skills   : {sorted(owned_set)}")
        print(f"partial_skills : {sorted(partial_set)}")
        print(f"skill_gaps     : {sorted(gap_set)}")
        if overlap_op or overlap_og or overlap_pg:
            print(f"❌ 중복 발생")
            if overlap_op: print(f"   owned ∩ partial = {overlap_op}")
            if overlap_og: print(f"   owned ∩ gaps    = {overlap_og}")
            if overlap_pg: print(f"   partial ∩ gaps  = {overlap_pg}  ← 이게 있으면 v6 버그")
        else:
            print("✅ 세 목록 완전 분리 확인 — 중복 없음")
