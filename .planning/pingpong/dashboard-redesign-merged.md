# Product Dashboard Redesign Merged Plan

Updated: 2026-05-21

## Objective

The dashboard must behave like a real job-application readiness product. The user provides a target job posting and their own candidate materials, chooses roadmap preferences, then receives skill-gap analysis, recommended learning resources, a weekly roadmap, and a report.

## Key Decision

The accepted product direction starts from real user inputs. The primary action is not to inspect a prepared result, but to analyze a target job posting against the user's own materials.

## Information Architecture

1. Job posting input: URL, pasted text, PDF/TXT.
2. Candidate material input: cover letter, resume, portfolio, GitHub README, PDF/TXT.
3. Roadmap preferences: target duration, current level, learning intensity.
4. Analysis progress: extract text, classify job, compare skills, retrieve resources.
5. Result summary: predicted job, fit score, missing skill count, top priority.
6. Evidence: required skills, owned skills, missing skills, gap scores.
7. Recommendations: learning resources grouped by missing skill.
8. Weekly roadmap and natural-language report.

## Visual Direction

Use restrained product UI. The first screen should feel like a career analysis tool: clear input panels, visible progress, score bars, evidence lists, resource rows, and a weekly timeline. Avoid internal role labels and debug controls in the normal user flow.

## Implementation Implication

Frontend changes alone are insufficient. The backend needs an `/analyze` flow that accepts raw job-posting and candidate inputs, calculates gaps, applies roadmap preferences, then calls the learning-resource recommendation pipeline.
