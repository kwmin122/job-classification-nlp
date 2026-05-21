from __future__ import annotations

from app.schemas import (
    COutput,
    MissingSkill,
    RoadmapItem,
    RoadmapPreferences,
    SkillRecommendation,
    WeeklyRoadmapItem,
)


def generate_report(
    c_output: COutput,
    skill_recommendations: list[SkillRecommendation],
    roadmap: list[RoadmapItem],
) -> str:
    if not skill_recommendations:
        return (
            f"지원자는 {c_output.predicted_job} 직무 기준으로 {c_output.fit_score:.0f}점의 "
            "적합도를 보이며, 현재 입력에서는 뚜렷한 부족 역량이 전달되지 않았습니다. "
            "부족 역량 정보가 추가되면 해당 역량을 기준으로 학습 자료를 추천할 수 있습니다."
        )

    top = skill_recommendations[0]
    top_resources = ", ".join(
        recommendation.resource.title for recommendation in top.recommendations[:2]
    )
    roadmap_lines = []
    for item in roadmap[:3]:
        roadmap_lines.append(
            f"{item.priority}. {item.skill}: {item.focus} ({', '.join(item.recommended_titles[:2])})"
        )

    return "\n".join(
        [
            f"지원자는 {c_output.predicted_job} 직무 기준으로 {c_output.fit_score:.0f}점의 적합도를 보입니다.",
            f"가장 우선적으로 보완할 역량은 {top.skill}입니다. gap score는 {top.gap_score:.0f}점이며, 중요도는 {top.importance}로 전달되었습니다.",
            f"근거: {top.evidence}",
            f"추천 시작 자료: {top_resources}",
            "학습 순서는 부족 정도가 큰 역량부터 개념 이해, 실습, 미니 프로젝트, 포트폴리오 정리 순서로 구성했습니다.",
            "우선 로드맵:",
            *roadmap_lines,
            "이 리포트는 입력된 역량 격차 점수와 큐레이션된 학습자료 DB 검색 결과를 바탕으로 생성된 설명입니다. 웹 전체 검색 결과가 아닙니다.",
        ]
    )


def generate_product_report(
    predicted_job: str,
    fit_score: float,
    missing_skills: list[MissingSkill],
    weekly_roadmap: list[WeeklyRoadmapItem],
    preferences: RoadmapPreferences,
) -> str:
    if not missing_skills:
        return (
            f"지원자는 {predicted_job} 직무 기준으로 {fit_score:.0f}점의 적합도를 보입니다. "
            "현재 입력에서는 뚜렷한 부족 역량이 확인되지 않았습니다. "
            "지원 자료에 프로젝트 성과와 사용 기술 근거를 더 구체적으로 작성하면 분석 신뢰도를 높일 수 있습니다."
        )

    top = sorted(missing_skills, key=lambda item: item.gap_score, reverse=True)[0]
    weeks = ", ".join(f"{item.week}주차 {item.goal}" for item in weekly_roadmap[:3])
    return (
        f"지원자는 {predicted_job} 직무 기준으로 {fit_score:.0f}점의 적합도를 보입니다. "
        f"가장 먼저 보완할 역량은 {top.skill}이며 gap score는 {top.gap_score:.0f}점입니다. "
        f"근거는 '{top.evidence}'입니다. "
        f"{preferences.duration_weeks}주 동안 현재 수준 {preferences.difficulty}, 학습 강도 {preferences.intensity} 기준으로 "
        f"{weeks} 순서로 학습하는 것을 추천합니다. "
        "이 리포트는 채용공고와 지원자 자료의 역량 격차, 그리고 큐레이션된 학습자료 DB 검색 결과를 바탕으로 생성되었습니다."
    )
