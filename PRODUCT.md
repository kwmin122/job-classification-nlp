# Product

## Register

product

## Users

The primary users are job seekers, NLP course teammates, and reviewers who need to understand how a job-description analysis result becomes concrete learning recommendations. A presenter uses the app locally to show a complete flow from skill gaps to learning resources, roadmap, and readable report without exposing internal team-role boundaries.

## Product Purpose

This product demonstrates a job-description skill-gap recommendation workflow. It accepts structured gap-analysis results, searches a curated learning-resource database, ranks recommended resources, generates a learning roadmap, and presents the result in a local dashboard. Success means the vertical slice runs end to end on localhost, uses at least 80 curated resources, and explains the recommendation logic without overstating the RAG scope.

## Brand Personality

Calm, credible, practical. The product should feel like a focused career analysis tool, not a marketing landing page or a generic AI chatbot. It should make the recommendation pipeline legible and defensible.

## Anti-references

Do not make it look like a SaaS landing page, a decorative AI dashboard, or a card-heavy template full of vague metrics. Avoid gradient text, glassmorphism, nested cards, dark-blue observability styling, and decorative charts that do not explain the recommendation.

## Design Principles

1. Show the pipeline, not magic: every recommendation should connect back to a skill gap, score, and source.
2. Keep the RAG claim honest: describe this as curated learning-resource DB retrieval, not open-web search.
3. Prioritize demo reliability: the app must work from sample data without paid APIs or GPUs.
4. Make academic evaluation easy: expose formulas, data fields, and outputs clearly.
5. Treat the dashboard as a work surface: dense enough for analysis, quiet enough for presentation.

## Accessibility & Inclusion

Target WCAG AA contrast, keyboard-reachable controls, visible focus states, and Korean-first labels with English technical terms where common. Use restrained motion and respect reduced-motion preferences.
