"""
증거 우선(v5) 엔진을 기존 C파트 API 계약(run_c_part_analysis dict)에 맞추는 어댑터.

v5는 채용공고(JD) 문장-지원자 문장 유사도가 아니라, 지원자 글을 증거 우선
(DID/SAID/NOISE)으로 먼저 읽어 코퍼스 직무 프로필과 정렬한다. 따라서 jd_input은
받되 점수 산정에는 사용하지 않는다(아키텍처상 의도). 출력은 기존 COutput 스키마와 동일.

매핑:
  fit_score      ← v5 fit
  predicted_job  ← 직무군 한글명
  required_skills← 코퍼스 직무 프로필(필수/우대)
  owned_skills   ← v5 OWNED (증거 span 포함)
  partial_skills ← v5 UNOBSERVABLE (expression_gap)
  skill_gaps     ← v5 GAP
"""
import os
from pathlib import Path
from . import engine as v5

# ──────────────────────────────────────────────────────────────────
# UI 블록 헬퍼
# ──────────────────────────────────────────────────────────────────

_LEVEL_KO = {"beginner": "입문", "intermediate": "기초", "advanced": "실무"}
_SAID_TAG_MAP = {
    "said_opinion":        "의견",
    "said_aspiration":     "입사 후 포부",
    "said_aspiration_mid": "입사 후 포부",
    "said_reflection":     "성찰",
    "said_external_subj":  "사회 이슈 의견",
    "said_motivation":     "지원동기",
    "said_other_opinion":  "의견",
    "said_capability":     "역량 주장",
    "default_said":        "일반 진술",
    "default":             "일반 진술",
}


def _infer_said_tag(feat: dict) -> str:
    for key in feat:
        if key in _SAID_TAG_MAP:
            return _SAID_TAG_MAP[key]
    return "일반 진술"


def _infer_said_reason(tag: str) -> str:
    reasons = {
        "의견":        "의견이나 판단 진술로, 직무 역량의 수행 근거가 아닙니다.",
        "입사 후 포부": "입사 후 포부 서술로, 현재 보유 역량의 근거가 아닙니다.",
        "성찰":        "성찰 또는 배움 서술로, 직접 수행 근거로 인정되지 않습니다.",
        "사회 이슈 의견": "사회 이슈에 대한 견해로, 실제 수행 경험 근거가 아닙니다.",
        "지원동기":    "지원 동기 또는 관심 표현으로, 직무 역량 근거로 보기 어렵습니다.",
        "역량 주장":   "역량 보유 주장이나 구체적 수행 근거 없는 서술입니다.",
        "일반 진술":   "구체적 수행 근거 없는 일반 진술입니다.",
    }
    return reasons.get(tag, "직접 수행 경험 근거가 확인되지 않습니다.")


def _res_to_ui_item(res: dict) -> dict:
    """search_resources 결과 → UI ResourceItem 포맷."""
    # res has: id, skill, title, url, level, reliability(1-5), estimated_time, match_type, score
    # Look up full resource row for type/free_or_paid/reason
    rid = res.get("id", "")
    full = next((r for r in v5.RESOURCES if r["id"] == rid), None)
    kind = full["type"] if full else "강의"
    price = full["free_or_paid"] if full else "무료"
    why = full["reason"] if full else res.get("skill", "")
    trust = min(100, res.get("reliability", 3) * 20)
    level_ko = _LEVEL_KO.get(res.get("level", "beginner"), "입문")
    return {
        "title": res.get("title", ""),
        "url": res.get("url", ""),
        "kind": kind,
        "level": level_ko,
        "price": price,
        "trust": trust,
        "why": why,
    }


def _infer_gap_type(skill: str, sc: dict, owned: dict) -> str:
    """
    GAP 스킬의 gap_type 추론 — 스킬별(per-skill)로 정직하게.
    gap_type ∈ {learning, evidence, explicit}
      - evidence: 그 스킬이 자료에 언급은 됐으나 직접 수행 근거가 부족
      - learning: 자료에서 그 스킬의 흔적 자체를 찾지 못함
    (이전 버그: 후보 단위 expression_gap 플래그로 모든 gap을 'expression'으로 묶어
     '경험 있어 보이나'라는 동일·부정확한 문구가 붙던 문제를 제거함.)
    """
    if skill in owned:   # 별칭/부분 매칭 등으로 자료에 등장은 함
        return "evidence"
    return "learning"    # 자료에서 그 역량의 근거를 찾지 못함


def _gap_note(gap_type: str, skill: str) -> str:
    notes = {
        "learning":   "공고 요구 역량이나, 자료에서 수행·학습 근거를 찾지 못했습니다",
        "evidence":   "언급은 있으나 직접 수행한 근거 문장이 부족합니다",
        "expression": "관련 경험은 보이나 사용 기술·역할·결과가 구체적으로 드러나지 않습니다",
        "explicit":   "지원자가 직접 부족하다고 언급했습니다",
    }
    return notes.get(gap_type, "근거 미확인")


def _strengths_to_adjacent(strengths: dict) -> list:
    """extract_strengths 결과 → UI adjacent 포맷."""
    adj = []
    for cat, hits in strengths.items():
        if not hits:
            continue
        # level: count of hits * tier bonus, capped at 100
        tier_bonus = 1.2 if hits[0][2] == "직무보조강점" else 0.8
        level = min(100, round(len(hits) * 20 * tier_bonus))
        note = hits[0][1]  # first evidence sentence slice
        adj.append({"cat": cat, "level": level, "note": note})
    # Sort by level desc
    adj.sort(key=lambda x: -x["level"])
    return adj


def _build_ui_block(
    job_key: str,
    korean: str,
    candidate_text: str,
    sc: dict,
    owned: dict,
    roadmap: dict,
    strengths: dict,
    opts: dict | None = None,
    job_info: dict | None = None,
    posting_skills: list | None = None,
) -> dict:
    """
    v5 엔진 출력을 window.DATA 형태의 ui 블록으로 변환.
    하드코딩 없음 — 모든 값은 엔진 출력 또는 파라미터에서 파생.
    ★ core/요구역량은 '사용자가 입력한 공고에서 추출한 실제 스킬(posting_skills)' 기준.
    """
    opts = opts or {}
    job_info = job_info or {}

    # ── job ──────────────────────────────────────────────────────
    prof = v5.ROLE_PROFILES.get(job_key, [])
    # 공고 기준: 입력 공고에서 추출한 실제 요구 스킬. 없을 때만 코퍼스 프로필 폴백.
    core_skills = (list(posting_skills)[:7] if posting_skills
                   else [p["skill"] for p in prof if p["importance"] == "필수"][:7])
    ui_job = {
        "title": job_info.get("title", korean),
        "company": job_info.get("company", ""),
        "group": korean,
        "confidence": job_info.get("confidence", 0),
        "core": core_skills,
        "source": job_info.get("source", "텍스트"),
    }

    # ── summary ───────────────────────────────────────────────────
    gap_count = len(sc["states"]["GAP"]) + len(sc["states"]["UNOBSERVABLE"])
    weeks_val = opts.get("duration_weeks", 4)
    level_val = opts.get("difficulty", "기초")
    intensity_val = opts.get("intensity", "보통")
    ui_summary = {
        "predictedJob": korean,
        "predictedConfidence": job_info.get("confidence", 0),
        "fit": sc["fit"],
        "gapCount": gap_count,
        "weeks": weeks_val,
        "level": level_val,
        "intensity": intensity_val,
    }

    # ── scoreBreakdown ────────────────────────────────────────────
    expr_count = len(sc["states"]["UNOBSERVABLE"])
    ui_score = [
        {
            "key": "tech",
            "label": "공고 스킬 적합도",
            "value": sc.get("technical_match", 0),
            "weight": "= 적합도",
            "tone": "good" if sc.get("technical_match", 0) >= 70 else ("warn" if sc.get("technical_match", 0) >= 40 else "bad"),
            "tip": "공고가 요구한 역량별로 실제 수행 근거가 있는지(직접 1.0·유사 0.6·학습 0.3·없음 0)를 평균한 값. 이 값이 곧 적합도입니다.",
        },
        {
            "key": "exp",
            "label": "경험 근거 강도 (참고)",
            "value": sc.get("experience_evidence", 0),
            "weight": "참고",
            "tone": "good" if sc.get("experience_evidence", 0) >= 65 else ("warn" if sc.get("experience_evidence", 0) >= 40 else "bad"),
            "tip": "지원자가 보여준 전체 경험의 강도(참고용). 적합도에 직접 가산하지 않으며, 공고 요구 역량을 실제로 수행했는지 판단하는 근거로만 사용됩니다.",
        },
        {
            "key": "adj",
            "label": "직무 외 강점 (참고)",
            "value": min(100, sum(1 for hits in strengths.values() if hits) * 15),
            "weight": "별도",
            "tone": "good",
            "tip": "PM·협업·자동화·운영처럼 직무 핵심 기술은 아니지만 참고할 강점. 적합도와 별개로 표시되며 점수에 가산되지 않습니다.",
        },
        {
            "key": "expr",
            "label": "표현 근거 부족",
            "value": expr_count,
            "unit": "건",
            "tone": "bad" if expr_count > 0 else "info",
            "isCount": True,
            "tip": "경험은 있어 보이나 사용 기술·본인 역할·결과가 불명확해, 근거로 충분히 인정되지 못한 문장의 수입니다.",
        },
    ]

    # ── competencies ──────────────────────────────────────────────
    importance_map = {p["skill"]: p["importance"] for p in prof}

    # met: OWNED skills with evidence
    ui_met = []
    for skill in sc["states"]["OWNED"]:
        ev = owned.get(skill, "")
        if ev and ev.startswith("_emb:"):
            ev = ""
        # Coverage: higher for mandatory skills with explicit evidence
        base_cov = 80 if importance_map.get(skill) == "필수" else 70
        cov_pct = base_cov + (5 if len(ev) > 30 else 0)
        ui_met.append({
            "skill": skill,
            "coverage": cov_pct,
            "type": "실제 프로젝트 경험" if ev else "직접 수행",
            "evidence": ev if ev else "—",
            "source": "자소서",
        })

    # partial: UNOBSERVABLE skills
    ui_partial = []
    for skill in sc["states"]["UNOBSERVABLE"]:
        ev = owned.get(skill, "")
        if ev and ev.startswith("_emb:"):
            ev = ""
        ui_partial.append({
            "skill": skill,
            "coverage": 35,
            "type": "이수 / 학습 근거",
            "evidence": ev if ev else "경험이 있을 수 있으나 기술스택 명시 부족",
            "verdict": "사용 기술·역할·결과를 구체적으로 표현할 것을 권장합니다.",
            "source": "자소서",
        })

    # gap: GAP skills
    ui_gap = []
    for skill in sc["states"]["GAP"]:
        gap_type = _infer_gap_type(skill, sc, owned)
        ev_text = owned.get(skill, "—")
        if ev_text and ev_text.startswith("_emb:"):
            ev_text = "—"
        ui_gap.append({
            "skill": skill,
            "gap": gap_type,
            "evidence": ev_text if ev_text else "—",
            "source": "—" if not ev_text or ev_text == "—" else "자소서",
            "note": _gap_note(gap_type, skill),
        })

    # adjacent: strength categories
    ui_adjacent = _strengths_to_adjacent(strengths)

    # ── excluded sentences ────────────────────────────────────────
    ui_excluded = []
    for sent in v5.split_sentences(candidate_text):
        label, feat = v5.classify_sentence(sent)
        if label == "SAID" and len(sent) > 15:
            tag = _infer_said_tag(feat)
            reason = _infer_said_reason(tag)
            ui_excluded.append({
                "text": sent,
                "reason": reason,
                "tag": tag,
            })
    # Keep at most 8 excluded items to avoid overwhelming the UI
    ui_excluded = ui_excluded[:8]

    # ── resources ─────────────────────────────────────────────────
    ui_resources = []
    for week in roadmap.get("weeks", []):
        skill = week["skill"]
        gap_type = week.get("gap_type", "learning")
        items = [_res_to_ui_item(r) for r in week.get("resources", [])]
        if items:
            ui_resources.append({
                "skill": skill,
                "gap": gap_type,
                "items": items,
            })

    # ── roadmap ───────────────────────────────────────────────────
    ui_roadmap = []
    for week in roadmap.get("weeks", []):
        resources = week.get("resources", [])
        res_titles = ", ".join(r.get("title", "") for r in resources[:2])
        ui_roadmap.append({
            "week": week["week"],
            "goal": f"{week['skill']} 학습 및 역량 강화",
            "skills": [week["skill"]],
            "res": res_titles or "—",
            "task": f"{week['skill']} 관련 프로젝트 구현 또는 개인 학습",
            "output": f"{week['skill']} 적용 결과물 또는 정리 노트",
        })

    # ── report ────────────────────────────────────────────────────
    owned_list = sc["states"]["OWNED"]
    gap_list = sc["states"]["GAP"]
    partial_list = sc["states"]["UNOBSERVABLE"]

    strengths_strs = []
    for cat, hits in strengths.items():
        if hits:
            strengths_strs.append(f"{cat} — {hits[0][1]}")

    gaps_strs = []
    for sk in gap_list:
        imp = importance_map.get(sk, "우대")
        gaps_strs.append(f"{sk}({imp}) — {_gap_note(_infer_gap_type(sk, sc, owned), sk)}")

    expr_strs = [
        f"{sk} — 사용 기술·역할·결과를 구체적으로 명시 필요"
        for sk in partial_list
    ]

    order_parts = [f"{i+1}주차 {w['skill']}" for i, w in enumerate(roadmap.get("weeks", [])[:4])]
    order_str = " → ".join(order_parts) if order_parts else "학습 로드맵을 확인하세요"

    expression_note = roadmap.get("expression_note")
    expr_strs_final = expr_strs if expr_strs else (
        [expression_note] if expression_note else []
    )

    report_summary = (
        f"현재 제출한 자료 기준으로 {korean} 직무 적합도는 {sc['fit']}점입니다. "
        + (f"보유 역량({', '.join(owned_list[:3])})은 확인됩니다. " if owned_list else "")
        + (f"핵심 요구 역량({', '.join(gap_list[:3])})의 직접 수행 근거가 충분하지 않습니다." if gap_list else "")
    )

    ui_report = {
        "summary": report_summary,
        "strengths": strengths_strs[:3] if strengths_strs else ["강점 근거가 충분히 확인되지 않았습니다."],
        "gaps": gaps_strs[:3] if gaps_strs else [],
        "expression": expr_strs_final[:2],
        "order": [order_str],
        "caution": [
            "이 점수는 지원자의 실제 능력을 단정하지 않고, 현재 제출한 자료에 드러난 근거만으로 계산되었습니다.",
            "자소서에 적힌 성과 수치는 검증된 성과가 아니라 '자소서상 주장'으로만 사용되었습니다.",
        ],
    }

    return {
        "job": ui_job,
        "summary": ui_summary,
        "scoreBreakdown": ui_score,
        "competencies": {
            "met": ui_met,
            "partial": ui_partial,
            "gap": ui_gap,
            "adjacent": ui_adjacent,
        },
        "excluded": ui_excluded,
        "resources": ui_resources,
        "roadmap": ui_roadmap,
        "report": ui_report,
    }

JOB_MAP = {
    "backend": "백엔드 개발자",
    "frontend": "프론트엔드 개발자",
    "ai": "AI/ML 엔지니어",
    "data_analyst": "데이터 분석가",
}


def normalize_skill_name(skill: str) -> str:
    return v5.ALIASES.get(skill, skill)


def _filter_analyzable_skills(skills):
    # v7 호환 시그니처 유지 (v5는 가제터 기반이라 그대로 통과)
    return list(skills)


def load_text(source: str) -> str:
    """문자열이면 그대로, 존재하는 .txt/.pdf 경로면 읽어서 텍스트로."""
    if not isinstance(source, str):
        return str(source)
    s = source.strip()
    # 너무 길면(>260) 경로일 수 없음 → 텍스트
    if len(s) <= 260 and os.path.exists(s):
        p = Path(s)
        if p.suffix.lower() == ".txt":
            return p.read_text(encoding="utf-8")
        if p.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader
            except Exception:
                from PyPDF2 import PdfReader
            return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    return source


def _gap_level(score: float) -> str:
    return "높음" if score >= 70 else ("중간" if score >= 40 else "낮음")


def run_c_part_analysis(
    b_predicted_job: str,
    jd_input: str,
    candidate_input: str,
    threshold: float = 0.45,
    *,
    explicit_required_skills=None,
) -> dict:
    try:
        job_key = (b_predicted_job or "").strip().lower()
        korean = JOB_MAP.get(job_key)
        if not korean:
            return {
                "status": "error",
                "message": (
                    f"B파트 라벨 '{b_predicted_job}'은 정의되지 않은 값입니다. "
                    f"허용값: {list(JOB_MAP.keys())}"
                ),
            }

        candidate_text = load_text(candidate_input)
        if not candidate_text or not candidate_text.strip():
            raise ValueError("지원자 서류 텍스트가 비어 있습니다.")

        owned, did, ach, emb_audit = v5.extract_owned(candidate_text, job_group=job_key)
        sc = v5.score(job_key, owned, did, ach, candidate_text, emb_audit=emb_audit)

        prof = v5.ROLE_PROFILES.get(job_key, [])

        # ★ 공고 기준 요구역량: 사용자가 입력한 공고에서 실제로 추출한 스킬.
        #   우선순위: (1) URL 정형 스킬(explicit) → (2) 공고 본문 가제터 추출 → (3) 코퍼스 폴백
        jd_text = load_text(jd_input) if jd_input else ""
        posting_skills: list[str] = []
        # 중복/상위어 정돈: 같은 역량의 표기 분산을 하나로 (예: ML·AI/ML→Machine Learning)
        _collapse = {"ML": "Machine Learning", "AI/ML": "Machine Learning", "데이터분석": "데이터 분석"}
        def _canon(s):
            # 원문 표기(예: 'Tensorflow')를 가제터 정규형('TensorFlow')으로 — 후보 보유 스킬과 매칭되게
            hits = v5.find_skills(s)
            return next(iter(hits.keys())) if hits else s
        def _dedup(skills):
            seen, out = set(), []
            for s in skills:
                c = _canon(s)
                c = _collapse.get(c, v5.ALIASES.get(c, c))
                if c not in seen:
                    seen.add(c); out.append(c)
            return out
        if explicit_required_skills:
            posting_skills = _dedup(explicit_required_skills)
        elif jd_text and len(jd_text.strip()) >= 20:
            posting_skills = _dedup(sorted(v5.find_skills(jd_text).keys()))
        required_from_posting = bool(posting_skills)
        if not posting_skills:  # 폴백(공고에서 못 뽑을 때만): 코퍼스 직무군 프로필
            posting_skills = [p["skill"] for p in prof if p["importance"] == "필수"]

        # ── 공고 요구 역량별 '실제 수행 근거' 충족도로 fit 계산 ──────────
        #   정책: fit = 공고 요구 역량별 충족 점수의 평균. 전체 경험 강도는
        #   fit에 직접 가산하지 않고, 각 요구 역량을 실제로 수행했는지의 근거로만 사용.
        #   역량별: 직접경험(DID) 1.0 / 유사(임베딩) 0.6 / 학습·언급 0.3 / 없음·포부·사회이슈 0
        cand_owned = {k for k in owned if not k.startswith("_emb:")}  # DID 근거 보유
        emb_groups = set(sc.get("emb_groups", []))
        SKILL_PARENT = v5.SKILL_PARENT
        # 기술 스택/활용 기술 섹션의 스킬도 '직접 경험'으로 인정 (이력서·불릿 스타일 보완).
        #   프로젝트에 나열한 기술은 실제 사용한 것으로 본다.
        _STACK_MARKERS = ("활용 기술", "활용기술", "사용 기술", "사용기술", "기술 스택",
                          "보유 기술", "사용 도구", "언어/라이브러리", "라이브러리",
                          "개발 환경", "tech stack", "skills", "stack")
        # 0점 처리할 SAID 유형(포부/지원동기/사회이슈/의견) — 그 외 언급은 0.3 인정
        _SAID_ZERO = {"said_aspiration", "said_aspiration_mid", "said_motivation",
                      "said_external_subj", "said_opinion", "said_other_opinion", "said_capability"}
        mentioned_non_said = set()
        for _sent in v5.split_sentences(candidate_text):
            _lbl, _feat = v5.classify_sentence(_sent)
            _low = _sent.lower()
            _is_stack = any(m in _low for m in _STACK_MARKERS)
            _hits = v5.find_skills(_sent)
            if _lbl == "DID" or _is_stack:
                for _sk in _hits:
                    cand_owned.add(_sk)            # 직접 경험으로 인정
                    owned.setdefault(_sk, _sent[:70])  # UI 증거로 해당 문장 사용
                continue
            if _lbl == "SAID" and any(k in _feat for k in _SAID_ZERO):
                continue                           # 포부/사회이슈/의견 → 0
            for _sk in _hits:
                mentioned_non_said.add(_sk)         # 학습·언급 → 0.3

        # 후보가 직접 보유한 스킬들의 상위 역량군(같은 군의 다른 스킬도 유사 경험으로 인정)
        cand_owned_parents = {SKILL_PARENT.get(k) for k in cand_owned if SKILL_PARENT.get(k)}
        met_p, partial_p, gap_p = [], [], []
        cov_scores = []
        for s in posting_skills:
            parent = SKILL_PARENT.get(s)
            if s in cand_owned:
                cov = 1.0; met_p.append(s)                 # 직접 수행 근거
            elif parent and (parent in emb_groups or parent in cand_owned_parents):
                cov = 0.6; partial_p.append(s)             # 유사 경험(같은 역량군: 임베딩 또는 동일군 스킬 보유)
            elif s in mentioned_non_said:
                cov = 0.3; partial_p.append(s)             # 학습·언급 수준
            else:
                cov = 0.0; gap_p.append(s)                 # 근거 없음(또는 포부/사회이슈에만)
            cov_scores.append(cov)
        fit_p = round(100 * sum(cov_scores) / len(cov_scores)) if cov_scores else 0

        # sc 오버라이드 → 이후 모든 UI/리포트가 공고 요구 역량 기준
        sc["states"] = {"OWNED": met_p, "GAP": gap_p, "UNOBSERVABLE": partial_p}
        sc["technical_match"] = fit_p   # 공고 스킬 적합도 = fit
        sc["fit"] = fit_p
        importance_map = {s: "필수" for s in posting_skills}

        # required_skills = 공고 기준
        required_skills = [
            {"skill": s, "importance": "필수",
             "source_sentence": ("공고 명시" if required_from_posting else "")}
            for s in posting_skills
        ]

        owned_named = sc["states"]["OWNED"]
        owned_skills = [{"skill": s, "evidence": owned.get(s, "")} for s in owned_named]
        matched_skills = list(owned_named)

        skill_gaps = []
        for s in sc["states"]["GAP"]:
            imp = importance_map.get(s, "우대")
            gs = 85.0 if imp == "필수" else 65.0
            skill_gaps.append({
                "skill": s, "gap_score": gs, "gap_level": _gap_level(gs),
                "importance": imp,
                "evidence": f"지원자 자료에서 '{s}' 역량의 수행 근거가 확인되지 않음",
                "coverage": 0.0,
            })

        partial_skills = []
        for s in sc["states"]["UNOBSERVABLE"]:
            imp = importance_map.get(s, "우대")
            partial_skills.append({
                "skill": s,
                "evidence": "실증 경험은 풍부하나 해당 기술 스택의 명시가 부족 (확인 불가)",
                "evidence_strength": "weak",
                "gap_score": 50.0, "gap_level": "중간", "importance": imp,
                "note": "expression_gap", "coverage": 30.0,
            })

        strengths = v5.extract_strengths(candidate_text)
        sc["group"] = job_key  # needed by build_roadmap importance ordering
        roadmap = v5.build_roadmap(sc)

        ui = _build_ui_block(
            job_key=job_key,
            korean=korean,
            candidate_text=candidate_text,
            sc=sc,
            owned=owned,
            roadmap=roadmap,
            strengths=strengths,
            posting_skills=posting_skills,
        )

        return {
            "status": "success",
            "predicted_job": korean,
            "fit_score": float(sc["fit"]),
            "required_skills": required_skills,
            "owned_skills": owned_skills,
            "matched_skills": matched_skills,
            "partial_skills": partial_skills,
            "skill_gaps": skill_gaps,
            "_meta": {
                "engine": "evidence-first-v5",
                "named_skills": sc["named_skills"],
                "emb_groups": sc.get("emb_groups", []),
                "did_count": did,
                "technical_match": sc.get("technical_match"),
                "experience_evidence": sc.get("experience_evidence"),
                "flags": sc.get("flags", []),
            },
            "ui": ui,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
