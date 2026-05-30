from __future__ import annotations

from app.schemas import (
    COutput,
    MissingSkill,
    PartialSkill,
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
    partial_skills: list[PartialSkill],
    weekly_roadmap: list[WeeklyRoadmapItem],
    preferences: RoadmapPreferences,
    owned_skills_count: int = 0,
    jd_quality: str = "ok",
) -> str:
    """
    리포트 구조:
    ① 직무 분류 + 적합도
    ② 요구 N개 중 충족 X / 보완 Y / 부족 Z
    ③ 최우선 보완 1~2개 + coverage%
    ④ 로드맵 요약 (주차별 상이 반영)
    """
    # weak JD: 결과 단정 표현 없이 경고 문구 (fit_score 포함 금지)
    if jd_quality == "weak":
        lines = [
            f"**예측 직무**: {predicted_job}",
            "",
            "⚠️ 이 공고에서 명확한 기술 요구를 찾지 못했습니다. "
            "개발 직무 공고인지 확인하거나 본문을 직접 붙여넣어 주세요.",
        ]
        return "\n".join(lines)

    # ① 직무·적합도
    lines = [
        f"**예측 직무**: {predicted_job}  |  **역량 적합도**: {fit_score:.0f}점",
        "",
    ]

    # ② 충족 현황
    total = owned_skills_count + len(partial_skills) + len(missing_skills)
    lines += [
        f"**역량 충족 현황** (공고 요구 {total}개)",
        f"- ✅ 충족 {owned_skills_count}개",
        f"- 🟡 보완 필요 {len(partial_skills)}개",
        f"- ❌ 부족 {len(missing_skills)}개",
        "",
    ]

    # ③ 최우선 보완 역량 (missing 상위 2개)
    top_missing = sorted(missing_skills, key=lambda x: x.gap_score, reverse=True)[:2]
    if top_missing:
        lines.append("**최우선 보완 역량**")
        for item in top_missing:
            cov = getattr(item, "coverage", 100 - item.gap_score)
            lines.append(f"- **{item.skill}** — 현재 충족도 {cov:.0f}%")
        lines.append("")

    # ④ 로드맵 요약
    if weekly_roadmap:
        lines.append(f"**{preferences.duration_weeks}주 학습 로드맵** ({preferences.difficulty} / {preferences.intensity})")
        for week_item in weekly_roadmap:
            lines.append(f"- {week_item.week}주차: {week_item.goal}")
        lines.append("")

    lines.append(
        "이 리포트는 채용공고와 지원자 자료의 역량 격차, 큐레이션된 학습자료 DB 검색 결과를 바탕으로 생성되었습니다."
    )

    return "\n".join(lines)
