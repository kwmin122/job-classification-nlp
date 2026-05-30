# backend/tools/measure_coverage_baseline.py
"""
"맨 스킬 단어 → 지원자 문장" 코사인 유사도 분포 측정.
coverage 재설계(Task 4)의 BASELINE/STRONG 값을 실측으로 결정한다.

실행:
  cd /path/to/nlp
  PYTHONPATH=backend .venv/bin/python backend/tools/measure_coverage_baseline.py
"""
from __future__ import annotations

import sys
sys.path.insert(0, "backend")

import numpy as np
from app.services.c_part.pipeline import get_embedding, cosine_sim

# 충족 케이스 (STRONG 후보 — "분명히 보유한 기술")
OWNED_PAIRS = [
    ("Python", "Python으로 데이터 파이프라인을 구축하고 FastAPI 백엔드를 개발했습니다."),
    ("Docker", "Docker와 docker-compose로 로컬 개발환경 및 CI 파이프라인을 구성했습니다."),
    ("React", "React와 TypeScript로 대시보드 SPA를 개발했습니다."),
    ("Node.js", "Node.js Express로 REST API를 설계하고 배포했습니다."),
    ("LLMOps", "LLMOps 워크플로우를 구축하여 LLM 모델 버전 관리 및 평가를 자동화했습니다."),
    ("AI Agent", "LangChain 기반 AI Agent를 개발해 자동화 태스크를 처리했습니다."),
]

# 무관 케이스 (BASELINE 이하여야 함)
UNOWNED_PAIRS = [
    ("Python", "Excel과 PowerPoint로 보고서를 작성했습니다."),
    ("Docker", "팀 미팅 일정을 조율하고 회의록을 작성했습니다."),
    ("LLMOps", "홍보 콘텐츠를 SNS에 게시하고 마케팅 캠페인을 진행했습니다."),
]

# 경계 케이스 (BASELINE~STRONG 사이 예상)
PARTIAL_PAIRS = [
    ("Docker", "Docker에 대한 기본적인 개념을 이해하고 있으며 팀에서 사용하는 것을 보았습니다."),
    ("React", "React 스터디에 참여했고 기초 문법을 공부했습니다."),
    ("LLMOps", "LLMOps 관련 유튜브 영상을 시청하고 개념을 파악했습니다."),
]


def main() -> None:
    print("[측정] Ko-SRoBERTa 로딩 중...")

    print("\n=== OWNED (충족 케이스) ===")
    owned_sims = []
    for skill, sent in OWNED_PAIRS:
        v_skill = get_embedding(skill)
        v_sent = get_embedding(sent)
        sim = cosine_sim(v_skill, v_sent)
        owned_sims.append(sim)
        print(f"  sim={sim:.3f}  skill={skill!r}  sent={sent[:50]!r}...")

    print("\n=== UNOWNED (무관 케이스) ===")
    unowned_sims = []
    for skill, sent in UNOWNED_PAIRS:
        v_skill = get_embedding(skill)
        v_sent = get_embedding(sent)
        sim = cosine_sim(v_skill, v_sent)
        unowned_sims.append(sim)
        print(f"  sim={sim:.3f}  skill={skill!r}  sent={sent[:50]!r}...")

    print("\n=== PARTIAL (경계 케이스) ===")
    partial_sims = []
    for skill, sent in PARTIAL_PAIRS:
        v_skill = get_embedding(skill)
        v_sent = get_embedding(sent)
        sim = cosine_sim(v_skill, v_sent)
        partial_sims.append(sim)
        print(f"  sim={sim:.3f}  skill={skill!r}  sent={sent[:50]!r}...")

    # 권장값 계산
    print("\n=== 권장 BASELINE/STRONG ===")
    baseline_candidate = max(unowned_sims) + 0.03 if unowned_sims else 0.25
    strong_candidate = float(np.percentile(owned_sims, 25)) if owned_sims else 0.55

    print(f"  OWNED sims:   {[round(s,3) for s in owned_sims]}")
    print(f"  UNOWNED sims: {[round(s,3) for s in unowned_sims]}")
    print(f"  PARTIAL sims: {[round(s,3) for s in partial_sims]}")
    print()
    print(f"  권장 BASELINE = {baseline_candidate:.3f}  (unowned_max={max(unowned_sims):.3f}+0.03)")
    print(f"  권장 STRONG   = {strong_candidate:.3f}  (owned_p25)")
    print(f"  EXP_BONUS     = 15")
    print()
    print("  → pipeline.py Task 4에서 COV_BASELINE/COV_STRONG을 위 측정값으로 설정하세요.")


if __name__ == "__main__":
    main()
