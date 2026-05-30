from __future__ import annotations

from app.schemas import RoadmapItem, RoadmapPreferences, SkillRecommendation

# ── Intensity → skill cap ─────────────────────────────────────────
INTENSITY_SKILL_CAP: dict[str, int] = {"가볍게": 3, "보통": 5, "집중": 7}

PHASES = ["기초 개념·환경 설정", "핵심 기능 실습", "미니 프로젝트 적용", "정리·면접 대비"]

# ── Practice matrix: intensity × difficulty_group ─────────────────
# difficulty_group: "beginner" = 입문/기초, "advanced" = 실무/심화
PRACTICE_MATRIX: dict[str, dict[str, list[str]]] = {
    "가볍게": {
        "beginner": [
            "유튜브 입문 영상으로 핵심 개념을 30분 이내 파악하기",
            "공식 예제 1개 따라 실행하고 결과 스크린샷 남기기",
            "{skill} 개념과 예시를 README 한 단락으로 정리하기",
            "면접 예상 질문 1개와 한 줄 답변 메모하기",
        ],
        "advanced": [
            "공식 문서에서 실무 관련 섹션만 빠르게 훑어 핵심 패턴 메모하기",
            "기존 프로젝트에서 {skill} 적용 가능한 부분 1곳 찾아 개선 아이디어 정리하기",
            "{skill} 오픈소스 코드 1개 분석하고 실무 적용 패턴 요약하기",
            "실무 경험 기반 면접 예상 질문 1개와 답변 초안 작성하기",
        ],
    },
    "보통": {
        "beginner": [
            "공식 문서·입문 강의로 핵심 개념 정리하고 개발 환경 구성하기",
            "공식 예제나 튜토리얼 따라 핵심 API 실습하기",
            "{skill}을 활용한 미니 프로젝트 만들고 README에 정리하기",
            "{skill} 면접 예상 질문 3개와 답변 근거 정리하기",
        ],
        "advanced": [
            "공식 문서·레퍼런스로 핵심 개념 정리하고 실무 환경에 셋업하기",
            "실무 패턴과 안티패턴을 분석하고 기존 코드에 적용해 보기",
            "{skill}을 실제 프로젝트에 도입해 개선 효과를 측정하고 문서화하기",
            "{skill} 심화 면접 질문 3개와 코드 예시 포함 답변 정리하기",
        ],
    },
    "집중": {
        "beginner": [
            "공식 문서 전체 정독 + 핵심 개념 요약 노트 작성 및 개발 환경 완전 구성하기",
            "튜토리얼 완주 후 핵심 기능 2개 이상 변형 실습하고 차이 분석하기",
            "{skill}을 사용하는 사이드 프로젝트 만들어 GitHub에 커밋·README 작성하기",
            "면접 예상 질문 5개 + 코드 예시 포함 답변 스크립트 완전 대비하기",
        ],
        "advanced": [
            "공식 문서 전체 + 관련 레퍼런스 정독, 내부 동작 원리 분석 노트 작성하기",
            "실무 코드베이스에 {skill} 도입·리팩토링하고 성능·구조 Before/After 측정하기",
            "오픈소스 {skill} 프로젝트에 기여하거나 실무 수준 구현체를 GitHub PR로 제출하기",
            "심화 기술 면접 질문 5개 + 트레이드오프·설계 결정 포함 답변 스크립트 완성하기",
        ],
    },
}


def _difficulty_group(difficulty: str) -> str:
    return "advanced" if difficulty in ("실무", "심화") else "beginner"


# ── Roadmap item helpers (for generate_roadmap) ───────────────────
def _focus_for_gap(gap_score: float) -> str:
    if gap_score >= 70:
        return "기초 개념부터 실습까지 빠르게 보완"
    if gap_score >= 40:
        return "실습 중심으로 증거 경험 보강"
    return "심화 자료로 포트폴리오 표현 보완"


def _focus_for_target(target_type: str, gap_score: float) -> str:
    if target_type == "partial":
        return "기존 경험을 실무 수준으로 보강"
    return _focus_for_gap(gap_score)


def _steps_for(skill: str, gap_score: float, difficulty: str = "기초") -> list[str]:
    advanced = difficulty in ("실무", "심화")

    if gap_score >= 70:
        if advanced:
            return [
                f"{skill} 공식 문서와 GitHub 저장소 분석해 내부 동작 원리 파악",
                f"{skill}을 실무 환경(CI/CD, 운영 이슈)과 연결해 적용 시나리오 정리",
                f"기존 프로젝트에 {skill} 도입하고 Before/After 성능·구조 비교",
                "면접에서 설명할 구체적 구현 경험과 트레이드오프 정리",
            ]
        return [
            f"{skill} 핵심 개념과 용어 정리",
            f"{skill} 입문 자료를 따라 하며 기본 실습 완료",
            f"{skill}을 작은 프로젝트에 적용",
            "실습 결과와 배운 점을 README 또는 포트폴리오에 정리",
        ]
    if gap_score >= 40:
        if advanced:
            return [
                f"{skill} 실무 사용 패턴과 안티패턴 분석",
                "기존 코드베이스에서 개선 포인트를 찾아 리팩토링 PR 작성",
                "면접에서 설명할 문제 상황, 해결 과정, 결과 수치 정리",
            ]
        return [
            f"{skill} 관련 실습 자료 2개 이상 완료",
            "기존 프로젝트에 해당 역량을 적용한 개선 기록 작성",
            "면접에서 설명할 수 있는 문제 상황, 해결 과정, 결과 정리",
        ]
    if advanced:
        return [
            f"{skill} 관련 레퍼런스(아키텍처 사례, 기술 블로그) 검토",
            "지원자 자료에 구체적인 성과 수치와 기술적 의사결정 배경 추가",
            "면접 예상 질문 5개 작성과 코드 레벨 답변 정리",
        ]
    return [
        f"{skill} 심화 자료로 부족한 표현 보완",
        "지원자 자료에 구체적인 도구, 역할, 결과 수치 추가",
        "면접 예상 질문 3개와 답변 근거 정리",
    ]


def _practice_project(skill: str, difficulty: str = "기초") -> str:
    if difficulty in ("실무", "심화"):
        return f"{skill}을 기존 프로젝트에 통합하고 개선 내용을 PR로 정리하기"
    return f"{skill}을 활용한 미니 프로젝트를 만들고, 실행 방법과 결과를 README에 정리하기"


# ── Main entry points ─────────────────────────────────────────────
def distribute_weeks(skills: list[str], preferences: RoadmapPreferences) -> list[dict]:
    """
    스킬을 duration_weeks 주차에 배분.

    - intensity  → 커버할 스킬 수 캡 + 주당 실습 깊이
    - difficulty → 실습 내용 수준 (beginner / advanced)
    - duration_weeks → 총 주차 수
    """
    if not skills:
        return []

    intensity = preferences.intensity
    difficulty = preferences.difficulty

    skill_cap = INTENSITY_SKILL_CAP.get(intensity, 5)
    d_group = _difficulty_group(difficulty)
    phase_practice = PRACTICE_MATRIX.get(intensity, PRACTICE_MATRIX["보통"])[d_group]

    duration = preferences.duration_weeks
    n_skills = min(len(skills), skill_cap)
    skills = list(skills[:n_skills])

    weeks_out = []

    if n_skills >= duration:
        # 주차당 1스킬 (상위 duration개만)
        for i in range(duration):
            skill = skills[i]
            weeks_out.append({
                "week": i + 1,
                "goal": f"{skill} — {PHASES[0]}",
                "skills": [skill],
                "practice": phase_practice[0],
            })
    else:
        # 각 스킬에 연속 주차 배분
        weeks_per_skill = duration // n_skills
        extra = duration % n_skills
        week_num = 1
        for idx, skill in enumerate(skills):
            alloc = weeks_per_skill + (1 if idx < extra else 0)
            for j in range(alloc):
                phase_idx = min(j, len(PHASES) - 1)
                phase = PHASES[phase_idx]
                practice = phase_practice[phase_idx].replace("{skill}", skill)
                weeks_out.append({
                    "week": week_num,
                    "goal": f"{skill} — {phase}",
                    "skills": [skill],
                    "practice": practice,
                })
                week_num += 1

    return weeks_out


def generate_roadmap(
    skill_recommendations: list[SkillRecommendation],
    difficulty: str = "기초",
) -> list[RoadmapItem]:
    sorted_items = sorted(
        skill_recommendations,
        key=lambda item: (0 if item.target_type == "gap" else 1, -item.gap_score),
    )

    roadmap: list[RoadmapItem] = []
    for index, item in enumerate(sorted_items, start=1):
        roadmap.append(
            RoadmapItem(
                priority=index,
                skill=item.skill,
                gap_score=item.gap_score,
                gap_level=item.gap_level,
                focus=_focus_for_target(item.target_type, item.gap_score),
                steps=_steps_for(item.skill, item.gap_score, difficulty),
                recommended_titles=[
                    recommendation.resource.title for recommendation in item.recommendations[:3]
                ],
                practice_project=_practice_project(item.skill, difficulty),
            )
        )
    return roadmap
