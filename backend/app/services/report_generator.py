from __future__ import annotations

from app.schemas import COutput, RoadmapItem, SkillRecommendation


def generate_report(
    c_output: COutput,
    skill_recommendations: list[SkillRecommendation],
    roadmap: list[RoadmapItem],
) -> str:
    if not skill_recommendations:
        return (
            f"지원자는 {c_output.predicted_job} 직무 기준으로 {c_output.fit_score:.0f}점의 "
            "적합도를 보이며, 현재 입력에서는 뚜렷한 부족 역량이 전달되지 않았습니다. "
            "C 파트의 skill_gaps 결과가 추가되면 해당 역량을 기준으로 학습 자료를 추천할 수 있습니다."
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
            "이 리포트는 큐레이션된 학습자료 DB 검색 결과를 바탕으로 생성된 설명이며, 실제 역량 판단은 C 파트의 gap score 입력에 의존합니다.",
        ]
    )

