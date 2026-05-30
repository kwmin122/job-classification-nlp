from __future__ import annotations

from app.schemas import RoadmapItem, RoadmapPreferences, SkillRecommendation


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


def _steps_for(skill: str, gap_score: float) -> list[str]:
    if gap_score >= 70:
        return [
            f"{skill} 핵심 개념과 용어 정리",
            f"{skill} 입문 자료를 따라 하며 기본 실습 완료",
            f"{skill}을 작은 프로젝트에 적용",
            "실습 결과와 배운 점을 README 또는 포트폴리오에 정리",
        ]
    if gap_score >= 40:
        return [
            f"{skill} 관련 실습 자료 2개 이상 완료",
            "기존 프로젝트에 해당 역량을 적용한 개선 기록 작성",
            "면접에서 설명할 수 있는 문제 상황, 해결 과정, 결과 정리",
        ]
    return [
        f"{skill} 심화 자료로 부족한 표현 보완",
        "지원자 자료에 구체적인 도구, 역할, 결과 수치 추가",
        "면접 예상 질문 3개와 답변 근거 정리",
    ]


def _practice_project(skill: str) -> str:
    return f"{skill}을 활용한 미니 프로젝트를 만들고, 실행 방법과 결과를 README에 정리하기"


PHASES = ["기초 개념·환경 설정", "핵심 기능 실습", "미니 프로젝트 적용", "정리·면접 대비"]

PHASE_PRACTICE = [
    "공식 문서·입문 강의로 핵심 개념을 정리하고 개발 환경을 구성하기",
    "공식 예제나 튜토리얼을 따라 핵심 API를 실습하기",
    "{skill}을 활용한 미니 프로젝트를 만들고 실행 방법과 결과를 README에 정리하기",
    "{skill} 면접 예상 질문 3개와 답변 근거를 정리하기",
]


def distribute_weeks(skills: list[str], preferences: RoadmapPreferences) -> list[dict]:
    """
    스킬을 duration_weeks 주차에 배분.
    - skills >= weeks: 주차당 1스킬 (상위 weeks개)
    - skills < weeks: 각 스킬에 연속 주차 배분 + PHASES 차등
    - 스킬 1개/4주: 4주 모두 같은 스킬이되 goal/practice가 PHASES[i]로 달라짐
    """
    if not skills:
        return []

    duration = preferences.duration_weeks
    n_skills = min(len(skills), 5)  # cap at 5 skills
    skills = list(skills[:n_skills])

    weeks_out = []

    if n_skills >= duration:
        # 주차당 1스킬 (상위 duration개만 사용)
        for i in range(duration):
            skill = skills[i]
            weeks_out.append({
                "week": i + 1,
                "goal": f"{skill} — {PHASES[0]}",
                "skills": [skill],
                "practice": PHASE_PRACTICE[0],
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
                practice = PHASE_PRACTICE[phase_idx].replace("{skill}", skill)
                weeks_out.append({
                    "week": week_num,
                    "goal": f"{skill} — {phase}",
                    "skills": [skill],
                    "practice": practice,
                })
                week_num += 1

    return weeks_out


def generate_roadmap(skill_recommendations: list[SkillRecommendation]) -> list[RoadmapItem]:
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
                steps=_steps_for(item.skill, item.gap_score),
                recommended_titles=[
                    recommendation.resource.title for recommendation in item.recommendations[:3]
                ],
                practice_project=_practice_project(item.skill),
            )
        )
    return roadmap
