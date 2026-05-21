from __future__ import annotations

from app.schemas import RoadmapItem, RoadmapPreferences, SkillRecommendation


def _focus_for_gap(gap_score: float) -> str:
    if gap_score >= 70:
        return "기초 개념부터 실습까지 빠르게 보완"
    if gap_score >= 40:
        return "실습 중심으로 증거 경험 보강"
    return "심화 자료로 포트폴리오 표현 보완"


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


def distribute_weeks(skills: list[str], preferences: RoadmapPreferences) -> list[dict]:
    if not skills:
        return []
    weeks = []
    for week in range(1, preferences.duration_weeks + 1):
        skill = skills[min((week - 1) * len(skills) // preferences.duration_weeks, len(skills) - 1)]
        weeks.append(
            {
                "week": week,
                "goal": f"{skill} 학습 및 실습",
                "skills": [skill],
                "practice": f"{skill}을 적용한 작은 결과물을 만들고 정리하기",
            }
        )
    return weeks


def generate_roadmap(skill_recommendations: list[SkillRecommendation]) -> list[RoadmapItem]:
    sorted_items = sorted(
        skill_recommendations,
        key=lambda item: item.gap_score,
        reverse=True,
    )

    roadmap: list[RoadmapItem] = []
    for index, item in enumerate(sorted_items, start=1):
        roadmap.append(
            RoadmapItem(
                priority=index,
                skill=item.skill,
                gap_score=item.gap_score,
                gap_level=item.gap_level,
                focus=_focus_for_gap(item.gap_score),
                steps=_steps_for(item.skill, item.gap_score),
                recommended_titles=[
                    recommendation.resource.title for recommendation in item.recommendations[:3]
                ],
                practice_project=_practice_project(item.skill),
            )
        )
    return roadmap
