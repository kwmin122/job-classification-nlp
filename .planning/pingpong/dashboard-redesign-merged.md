## Objective

Ship a product-facing dashboard for JD-based skill-gap learning recommendations. The browser UI should speak to a job seeker or evaluator, not to an internal team-role handoff.

## Information Architecture

Use a product top bar for the promise: `지원 직무에 맞춘 학습 로드맵`.

Use a two-column work surface:

1. Left rail: analysis data, sample load, analyze action, local DB method note.
2. Right workspace: personalized improvement plan, summary metrics, gap table, resources, roadmap, report.

Keep method transparency, but place it in low-friction chips and the report's `분석 방법` block.

## Visual System

Use the product register: restrained light UI, native font stack, stable table/timeline surfaces, one teal accent, modest shadows, and 8px product-scale radii. Remove decorative radial background and large demo-card styling.

## Component Changes

- `page.tsx`: add product top bar and dashboard grid; remove internal module heading.
- `JsonInputPanel.tsx`: replace contract/team copy with analysis input copy.
- `SummaryStrip.tsx`: use user-facing metric labels.
- `GapMatrix.tsx`: make empty state and table labels product-facing.
- `ResourceRecommendations.tsx`: use recommendation copy rather than retrieval jargon in headings.
- `RoadmapPanel.tsx`: emphasize execution sequence.
- `ReportPanel.tsx`: rename formula area to analysis method.
- `layout.tsx` and `report_generator.py`: remove visible internal-module wording.
- `PRODUCT.md` and `DESIGN.md`: update durable design context so future passes do not reintroduce the internal framing.

## Copy Changes

Primary copy set:

- `지원 직무에 맞춘 학습 로드맵`
- `채용공고와 지원자 자료의 격차를 바탕으로 먼저 보완할 역량과 검증 가능한 학습 자료를 제안합니다.`
- `채용 준비 데이터`
- `분석 데이터 JSON`
- `보완 필요 역량`
- `역량별 추천 자료`
- `우선순위 학습 로드맵`
- `분석 방법`

## Risks

The raw JSON field still reveals the structured demo contract. This is acceptable for the current local vertical slice, but the primary path should be sample load plus analyze. A later full product should replace JSON with JD/resume text inputs once the upstream analysis module is integrated.

## Verification

Run `rg` for visible internal labels, run backend unit tests, run `npm run build`, and check local health/page endpoints.
