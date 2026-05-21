# Product Dashboard Redesign Note A

Updated: 2026-05-21

The dashboard should start from real user inputs:

- Job posting URL, pasted text, or PDF/TXT.
- Candidate cover letter, resume, portfolio, GitHub README, or PDF/TXT.
- Roadmap preferences: duration, current level, and learning intensity.

The UI should make `분석 시작` the primary action. It should keep the normal flow focused on the user's job target, candidate evidence, shortage diagnosis, and next learning steps.

The backend must produce the gap analysis before recommendation. Resource retrieval and roadmap generation remain downstream services that use the measured missing skills and user preferences.
