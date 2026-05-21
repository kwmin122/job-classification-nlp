## Objective

Make the dashboard feel like a real product for `역량 격차 기반 학습 추천`. The user should understand the product promise without knowing the team split behind it.

## Information Architecture

Keep the two-column layout: left rail for analysis input, right workspace for outputs. The result workspace should lead with the user's outcome, then show gap severity, recommended resources, roadmap, and a final explanation. RAG scope belongs in a small method disclosure.

## Visual System

Flatten the surface. Remove decorative glow, reduce panel radius to product-scale values, lower shadows, and keep teal for primary actions and top-priority emphasis. Avoid turning resource recommendations into a marketing grid.

## Component Changes

Update `JsonInputPanel`, `page.tsx`, `GapMatrix`, `ResourceRecommendations`, `RoadmapPanel`, `ReportPanel`, `layout.tsx`, and `report_generator.py`. Internal type names can remain in code, but browser-rendered labels should not expose team modules.

## Copy Changes

Preferred language: `분석 데이터 입력`, `역량 격차 학습 추천`, `분석 결과 JSON`, `입력 결과 해석`, `부족 점수 높은 순`, `추천 점수 높은 순`, `분석 리포트`, and `분석 방법`. Explain that the app searches a curated local learning-resource DB, not the open web.

## Risks

Raw JSON remains a local demo affordance, so the interface should make sample execution the friendliest path. Default ports may conflict on this machine, so demo instructions should mention alternate ports.

## Verification

Run a forbidden-string search for visible labels, run the Next build, run backend tests, and verify the local page still calls `/sample` and `/recommend` successfully.
