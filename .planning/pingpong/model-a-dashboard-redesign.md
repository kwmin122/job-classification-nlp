## Objective

Reframe the dashboard from an internal team-module demo into a Korean-first product surface for job-description skill-gap learning recommendations. Keep the current local JSON/sample flow and curated-resource retrieval logic, but remove visible team-role language from the browser UI.

## Information Architecture

Keep the existing work surface order because it matches the task: analysis input, summary, gap matrix, recommendations, roadmap, and report. The main issue is naming and hierarchy, not missing capability. Put technical method details in the report method block instead of the page header.

## Visual System

Use the existing restrained light OKLCH theme, but reduce the demo-like radial background, large radii, and heavy shadows. Preserve tables, score bars, resource rows, and the roadmap timeline because they explain the system better than decorative cards.

## Component Changes

Rename the input panel to analysis data input. Rename the main result area to a user-facing personalized improvement plan. Update the gap matrix empty state and section label. Update recommendation and roadmap labels. Remove internal role wording from page metadata and generated report text.

## Copy Changes

Use labels such as `분석 입력`, `채용 준비 데이터`, `분석 데이터 JSON`, `보완 필요 역량`, `역량별 추천 자료`, `우선순위 학습 로드맵`, and `분석 방법`. Keep RAG, embedding, and scoring terminology only as method metadata.

## Risks

Frontend-only cleanup is insufficient because backend-generated report text is visible in the report panel. Product context files also need to stop reintroducing the internal framing in future design passes.

## Verification

Search visible UI strings for internal role labels, build the frontend, run backend tests, and confirm sample analysis still produces recommendations, roadmap, and report.
