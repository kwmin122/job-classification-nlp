# Model A Dashboard Redesign Note

Updated: 2026-05-21

The product-facing direction is not merely to rename a JSON demo. The dashboard should start from real user inputs:

- Job posting URL, pasted text, or PDF/TXT.
- Candidate cover letter, resume, portfolio text, or PDF/TXT.

The UI should make `분석 시작` the primary action. It should not expose seeded data controls or precomputed gap contracts in the normal user flow.

The backend must produce the gap analysis before recommendation. Existing resource retrieval and roadmap generation can remain as downstream services.
