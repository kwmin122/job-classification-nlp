# Design

## Design System Overview

The interface is a local product dashboard for an academic NLP/RAG project. It uses a restrained light theme, clear tables, progress bars, badges, and a timeline. Visual polish should support explanation and trust rather than decoration.

## Color

Use OKLCH colors through CSS custom properties.

- Background: warm-tinted neutral, not pure white.
- Surface: slightly raised neutral panels with low-contrast borders.
- Text: ink-like neutral, not pure black.
- Primary accent: deep teal for actions, active states, and the highest-priority learning path.
- Secondary accents: muted amber for medium gaps, muted red for high gaps, slate-blue for informational tags.
- Success: restrained green.
- Warning: amber.
- Error: red with low-chroma background tint.

## Typography

Use a system UI stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif`. Keep type sizes fixed, not viewport-scaled. Favor compact product hierarchy:

- Page title: 28px, 700 weight.
- Section title: 16px to 18px, 700 weight.
- Body: 14px to 15px.
- Labels and metadata: 12px to 13px.
- Data numbers: tabular numerals.

## Layout

The primary layout is a responsive two-column work surface:

- Left rail: input JSON, sample controls, pipeline notes.
- Main area: summary strip, gap matrix, recommendations, roadmap, report.
- Desktop: left rail around 360px, main area fills the rest.
- Tablet/mobile: stack input first, then results.

Cards are used only for grouped repeated items such as individual recommended resources. Avoid nested cards. Prefer tables, bands, and timeline rows for structured information.

## Components

- Summary strip: compact metric tiles for predicted job, fit score, gap count, and top priority.
- Gap matrix: table with score bars, importance badges, evidence text, and status.
- Resource recommendation rows/cards: title, type, level, language, reliability, recommend score, reason, URL.
- Roadmap timeline: ordered stages by priority and learning step.
- Report panel: generated Korean summary with clear sections.
- JSON input panel: textarea, sample load button, analyze button, validation message.

## Interaction

- Primary action: analyze sample or pasted C output.
- Hover states should clarify clickable resource links and buttons.
- Focus-visible styles are required for buttons, links, and textarea.
- Loading should use skeleton-like inline states or disabled buttons, not modal spinners.
- Errors should be inline and specific.

## Motion

Use short 150-220ms transitions for hover, focus, panel reveal, and score bars. Avoid page-load choreography and layout-property animation. Respect `prefers-reduced-motion`.

## Content

Labels are Korean-first. Technical terms like RAG, gap score, Top-K, CSV, TF-IDF may remain English. Copy should be concise and explicit about what is proven by the demo.
