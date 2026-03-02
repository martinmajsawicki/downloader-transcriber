# Brand Guidelines — Copysight for macOS

Working document v0.3 — Minimalist Archive direction

---

## 1. Brand Essence

**One sentence:** You don't have time to watch everything — but you can't afford to miss anything.

**Core promise:** In 2 minutes, you know if 2 hours are worth it.

**Brand feeling:** The calm confidence of someone who's already read the brief before the meeting started.

## 2. Brand Personality

Think of the app as a brilliant, quiet analyst who sits next to you — no noise, no cheerfulness, no gamification. Just precise, fast, useful output. It has the energy of a well-designed newsroom tool: purposeful, professional, slightly minimal.

**Three personality anchors:**

- **Precise** — nothing decorative, nothing vague. Every word in the UI earns its place. The output is clean. The experience is surgical.
- **Calm** — not exciting, not alarming. The app works quietly in the background and returns with exactly what you asked for. Like a good editor: does the work, doesn't make drama.
- **Empowering** — the user finishes an interaction feeling smarter and more in control. There's a quiet pride in having the note ready when others are still halfway through the video.

## 3. Brand Position

**Category:** Personal knowledge infrastructure. Not a summarizer. Not a transcription tool. A personal intelligence layer.

**For:** People who consume content professionally — journalists, consultants, researchers, curious executives. People with too many subscriptions and not enough hours. People who feel behind.

**Against:** Noise, backlog guilt, FOMO, passive scrolling, wasted attention.

**Differentiator:** Local-first, private, personal. Your notes. Your machine. Your edge. Not a SaaS. Not a subscription. Yours.

## 4. Visual Direction

### Core Concept & Aesthetic

**The Aesthetic:** "Minimalist Archive" — warm analog materials, editorial clarity.

**The Vibe:** Austin Kleon's filing cabinet meets a high-end literary magazine. Warm and tactile on Screens 1-2 (the mechanical input), clean and typographic on Screens 3-4 (the reading and archiving). The skeuomorphism is restrained — it's a cue, not the whole show.

**Materials:** Manila paper, rubber stamps, permanent markers (Screens 1-2). Clean editorial whitespace, serif typography (Screens 3-4). The transition from input to output mirrors going from the workshop to the reading room.

### Mood references

- Austin Kleon's filing cabinet — physical folders, handwritten labels, productive chaos
- High-end editorial magazine layouts — typographic hierarchy, pull-quotes, structured grids
- Vintage office machinery — rubber stamp marks, typewriter output, mechanical switches
- Analog knowledge systems — Zettelkasten card indexes, library catalog drawers
- Neo-skeuomorphic macOS design — tactile surfaces with modern clarity

### Color Palette: "Minimalist Archive" Set

| Token | Name | Hex | Usage |
|-------|------|-----|-------|
| BASE | Matte Paper | `#F7E9C1` | Main window background. Very subtle fine grain noise on Screens 1-2; clean/smooth on Screens 3-4. |
| PRIMARY | Accent Red | `#D1344B` | "Nipple" button (Screen 1), stamp date (Screen 3), minimalist use only. |
| SECONDARY | Archive Blue | `#4A89C5` | Sidebar folder tabs (Screen 4). |
| HIGHLIGHT | Dusty Gold | `#E5B742` | Sidebar "Gold" tab (Screen 4), key insight markers. |
| TEXT | Ink Black | `#2B2B2B` | High-contrast, matte black. Avoid `#000000`. |

### Typography Stack (resolved)

| Role | Family | Usage |
|------|--------|-------|
| Headers / Branding | **IBM Plex Sans** (Bold / Condensed) | App name "COPYSIGHT", section headers (Praktyka, Obserwacje, Prognozy), sidebar tab labels, list titles. Modern, clean label feel. |
| Body / Reading | **Charter** or **Georgia** (serif) | Screen 3 reading experience — the three editorial paragraphs. Large interline (leading), wide margins, high readability. Elevated, academic, editorial. |
| UI / Metadata | **IBM Plex Mono** | Status stamps (Screen 2), search bar placeholder, dates in library list, page numbers, timestamps. Typewriter output feel. |

### Iconography / Logo Direction

Built around the concept of filing, archiving, and sight. The name "Copysight" bridges "copy" (journalistic clipping, editorial content) with "sight" (insight, foresight, oversight). No generic play buttons or video iconography — this lives in the world after the video.

## 5. Name: Copysight

**Resolved.** Copysight = Copy (journalistic clipping, content) + Sight (insight, foresight, oversight).

Previous candidates (Clipsight, Synthex, Notula, Voxlog, Podex) evaluated and retired. Verification method documented in `brand/naming-verification-method.md`.

## 6. Voice & Tone

### UI copy

Short. Declarative. No exclamation marks. No "Great job!" No onboarding cheerfulness. The app respects that you're busy.

**Right tone examples:**

- "Paste URL to begin." (not "Let's get started!")
- "Extracting insights." (not "Hang tight, working on it!")
- "Note saved." (not "Your summary is ready!")
- "3 steps. You choose how deep." (not "Customize your experience!")

### Marketing copy

First-person plural only when it earns it. Mostly second-person direct. Short sentences. Journalist's instinct — lead with the consequence, not the feature.

**Example:** "Two minutes. Nine insights. You decide if it's worth your afternoon."

## 7. Core User Experience Principles

**No celebration, no gamification.** The reward is the note itself. The app doesn't congratulate you. You did the smart thing — the note is the proof.

**Local is a feature, not a limitation.** Privacy and ownership are explicit brand values. Lean into this, especially for the target audience. "Stays on your machine" is not a footnote — it's a selling point.

**The library matters as much as the extraction.** The growing archive of past notes is part of the brand promise. Over time, the app becomes your personal knowledge layer. This needs to feel like a growing asset, not a log.

**Speed is felt, not advertised.** The 2-minute result shouldn't be promised in marketing — it should be experienced and then talked about by users. The interface should make the wait feel precise, not anxious.

## 8. Personal Brand Connection

The app is an extension of your professional identity: a journalist who doesn't just use AI tools — who builds them for a specific, real problem he faces every week. This is the story.

**The framing:** "I built this because I have 40 tabs open and 6 hours of video to watch before my next interview. So I made it do the work for me."

The app should credit you subtly — in the About screen, in the documentation, in the way it's released. Not aggressively, but unmistakably.

---

## 9. Workflow (resolved)

### The One-Click Pipeline

The red button triggers the entire pipeline. No intermediate decisions, no separate steps. One click = URL → Download → Transcribe → Analyze → Read.

```
Screen 1 (Input Desk)
  │  User pastes URL, clicks the red button
  │
  ▼
Screen 2 (Stamping)
  │  Connecting... → Downloading... → Transcribing... → Analyzing...
  │  Stamps appear sequentially, full pipeline runs automatically
  │
  ▼
Screen 3 (Reader)                    Screen 4 (Library)
  │  Auto-transition when analysis     ←→  Arrow key / trackpad swipe
  │  completes. Cross-dissolve from         navigates between Reader
  │  stamps to editorial text.              and Library.
```

### Screen Transitions

1. **Screen 1 → Screen 2:** Instant. Red button press starts the pipeline. URL slot shows "Connecting..." state.
2. **Screen 2 → Screen 3:** Automatic. When Analyzing completes, stamps dissolve and Reader content fades in. No user action required.
3. **Screen 3 ↔ Screen 4:** Manual. Arrow key (← →) or trackpad horizontal swipe. The Reader and Library are siblings — swipe left for Library, swipe right for Reader.
4. **Screen 4 → Screen 3:** Click a fiszka in the Library list to open it in the Reader (with sidebar visible).
5. **Screen 3/4 → Screen 1:** Always accessible. New URL input returns to the Input Desk.

### Transcription Visibility

Transcription is a processing artifact, not a user-facing product. It is:
- Saved automatically as a local `.txt` file in `downloads/transcripts/`
- Not visible in the UI — the Reader shows only the AI analysis (3-paragraph fiszka)
- Available for power users who want to reference the raw text, export to Obsidian, or re-analyze

The UI commitment: **what you see is the editorial result, not the raw material.**

### Sidebar Tabs: Age-Based Filing System

The sidebar tabs represent time-based views of the archive — like patina on paper, the older the fiszka, the warmer the color. Four age brackets:

| Tab | Age Range | Color | Hex | Metaphor |
|-----|-----------|-------|-----|----------|
| **Fresh** | Last 7 days | Ink Black | `#2B2B2B` | Fresh ink — just written, still drying |
| **Recent** | 8-30 days | Archive Blue | `#4A89C5` | Filed away — in the active drawer |
| **Settled** | 1-6 months | Accent Red | `#D1344B` | Settled into the archive — the worn folder |
| **Gold** | 6+ months | Dusty Gold | `#E5B742` | Aged knowledge — proven value over time |

Fiszki automatically move between tabs as they age. No manual sorting required. The metaphor: knowledge gains patina with time. What survives 6 months in your archive is gold.

---

## Design Decisions (internal notes)

### Chosen direction: Analog Archive — Neo-Skeuomorphism

**Pivot from v0.1:** Direction D "Lupek/Slate" (dark intelligence terminal) retired. New direction inspired by Austin Kleon's physical filing systems — warm, tactile, mechanical.

- **Surface:** Manila Cream (`#F7E9C1`) with fine grain noise — warm cardstock texture
- **Primary action:** Filing Red (`#D1344B`) — the rubber stamp, the big button
- **Navigation:** Archive Blue (`#4A89C5`) — folder tabs, structural borders
- **Highlight:** Dusty Gold (`#E5B742`) — extracted gold, key insights
- **Text:** Ink Black (`#2B2B2B`) — permanent marker energy, matte finish
- **Name:** Copysight (resolved)

### Typography system (resolved)

- **IBM Plex Sans** (Bold / Condensed) = branding ("COPYSIGHT"), section headers (Practical Insights, Observant Analysis), library list titles. Modern, clean label feel.
- **Charter** or **Georgia** (serif) = reading experience on Screen 3 — the editorial paragraphs. Large interline, wide margins, high readability. Academic, editorial elevation.
- **IBM Plex Mono** = status stamps (Screen 2), search bar placeholder, dates in library list, page numbers, timestamps. Typewriter output feel.

### UI Screens & Elements

#### Screen 1: The Input Desk

- **The "Nipple" Button:** 3D-modeled, circular red rubber button with soft radial gradient and 2px hard drop shadow. Accent Red (`#D1344B`). Positioned to the right of the URL slot.
- **The URL Slot:** An inset "groove" in the manila background that looks physically recessed. Shadow inward, no border — the slot is carved into the desk surface.
- **Title:** "COPYSIGHT" in bold condensed sans (IBM Plex Sans Bold), large, centered above the slot.
- **Background:** Matte Paper (`#F7E9C1`) with watercolor gear stains — static, blurred, warm-toned (`#B8A070`), like faded stamp prints soaked into the paper. Clusters in upper-right (large + small interlocking) and upper-left (single, more faded). Not mechanical — decorative, like aged watermarks on cardstock.
- **State:** Minimal — just the name, the slot, the button. Zero text instructions, zero labels. The affordance is physical.

#### Screen 2: The Mechanical Process (Stamping)

Two-phase transition from Screen 1 to Screen 3:

**Phase 1 — Full-screen stamps:** Each status label appears large and centered, one at a time, typewriter-style:
- "Connecting..." (takes over the full window, large monospace text)
- Watercolor gear stains visible in the background (same as Screen 1, static)

**Phase 2 — Stamp sequence with transition:** All four stamps stack vertically, centered:
- Connecting...
- Downloading...
- Transcribing...
- Analyzing...
- Each appears with a "stamp" animation — sudden opacity shift (0→100) with slight jitter / ink-bleed effect on font edges.
- Font: IBM Plex Mono, large size, Ink Black.
- Sound-wave icon appears in bottom-right corner during processing.
- As Analyzing completes, the stamps begin to dissolve and the Reader content (Screen 3) fades in underneath — a visual cross-dissolve from mechanical process to editorial result.

**Persistent elements during processing:** The red button and URL slot remain visible. Watercolor gear stains persist in background (static, unchanged).

#### Screen 3: The Reader (The Document)

A clean, vertical digital paper sheet. No cards, no grids.

- **Background:** Clean Matte Paper (`#F7E9C1`), smooth — very subtle noise only, almost imperceptible. The reading surface is calm.
- **Layout:** Wide margins, text centered (essay/editorial layout). Max-width ~600px content column.
- **Date stamp:** Small red stamp "01 MAR 2026" in the upper-right corner — the only skeuomorphic accent. Monospace (IBM Plex Mono), Accent Red (`#D1344B`).
- **Content:** Three editorial paragraphs, each a complete thought:
  - **Paragraph 1 — Practical Insights:** Opens with bold serif section header ("**Practical Insights**") inline with the body text. Actionable takeaways.
  - **Paragraph 2 — Observant Analysis:** Opens with bold serif header ("**Observant Analysis**"). Deeper observations, patterns noticed, context.
  - **Paragraph 3 — Predictions:** Forward-looking analysis, trends, implications.
- **Typography:** Charter or Georgia serif exclusively. Large interline (leading ~1.6-1.8), high readability. Section headers are bold inline, not separate — the text flows as one continuous reading experience.
- **Decorative elements:** Watercolor gear stains at very low opacity in the upper-right background (same as Screens 1-2, maintaining visual continuity). Static, blurred, part of the paper surface.
- **No sidebar** on initial view — the Reader is a focused, distraction-free reading experience.

**Alternative clean variant (with sidebar):** When navigating from Library, the Reader shows with the sidebar tabs visible on the left edge. In this mode: no gears, no sound icon — pure text on paper. The sidebar provides context (which fiszka you're reading from which collection).

#### Screen 4: The Library (The Archive)

Simplified, flat content management view.

- **Search bar:** Thin black outline (1px) or simple underline, with "Search..." placeholder in IBM Plex Mono. Zero 3D effects, zero shadows. Clean and functional.
- **File list:** Clean, text-based rows. Each row contains:
  - **Title:** Video title in IBM Plex Sans (bold). Left-aligned.
  - **Date:** Processing date in IBM Plex Mono. Right-aligned.
- **Row separator:** Subtle hairline or generous whitespace between rows. No cards, no borders.
- **Sidebar:** Vertical staggered folder tabs on the left edge — age-based filing system: Fresh (Ink Black `#2B2B2B`), Recent (Archive Blue `#4A89C5`), Settled (Accent Red `#D1344B`), Gold (Dusty Gold `#E5B742`). Flat colored rectangles with white rotated text. No deep shadows — just color blocks with 4px-8px radius. Fiszki move between tabs automatically as they age.
- **Background:** Matte Paper (`#F7E9C1`), clean — minimal to no noise. The list IS the content.

### Output format: 3-paragraph structure

- **Paragraph 1:** Practical Insights — actionable tips and takeaways
- **Paragraph 2:** Observant Analysis — patterns, context, deeper observations
- **Paragraph 3:** Predictions — forward-looking analysis, trends, implications
- **Presented as a continuous editorial document** — serif typography, wide margins, essay layout
- Section headers bold inline (not separate), text flows as one reading experience
- **Unit of knowledge = 1 fiszka per video** (containing 3 paragraphs of analysis)
- Library counts fiszki (per video), not individual insights
- Output ready for Obsidian export (markdown structure beneath the visual layer)

### Tactile Details (The Polish)

**Screens 1-2 (Input & Processing) — skeuomorphic:**
- Physical 3D button with multi-stop radial gradient and heavy contact shadow
- Recessed URL slot with inward shadow
- Watercolor gear stains — static, blurred (1-2px), warm brown (`#B8A070`), soaked into the paper like aged watermarks. Not animated. Clusters: right (large + small interlocking), left (single, fainter), bottom accent.
- Stamp animation with ink-bleed / jitter effect
- Paper grain noise on manila surface (~6% opacity)

**Screens 3-4 (Reader & Library) — minimalist:**
- Zero 3D effects. Flat, clean surfaces.
- The only analog accent on Screen 3: the small red date stamp in the corner.
- Sidebar tabs: flat colored rectangles, no deep shadows. 4px-8px radius.
- Search bar: thin 1px outline, no skeuomorphism.
- Wide whitespace as the primary structural element.

**Shared:**
- **Corners:** "Natural Rounding" — 4px-8px radius on tabs and interactive elements.
- **Vibrancy:** Optional warm macOS vibrancy on sidebar to let desktop wallpaper subtly tint the folder tabs.

### Key metaphors

- **Fiszka** — one complete extraction from one video (3 editorial paragraphs). The unit of knowledge.
- **The Desk** — Screens 1-2. The manila surface where you feed in material and the machine stamps through it.
- **The Reading Room** — Screen 3. Clean, quiet, typographic. You've left the workshop — now you read the result.
- **The Filing Cabinet** — Screen 4. Sidebar tabs for collections, flat list of accumulated fiszki. The growing archive.
- **The Stamp** — the mechanical process (Screen 2). Each step stamps its completion. The only animated skeuomorphic element.
- **The Date Stamp** — small red stamp on Screen 3. The artifact's birth certificate.

### Planned features (backlog)

- **Natywny eksport do Obsidian** — dwa tryby:
  1. Polished transcription (oczyszczona transkrypcja jako notatka .md)
  2. 3-paragraph fiszka jako structured note z tagami/linkami
  - Format: Markdown kompatybilny z Obsidian (YAML frontmatter, wikilinki opcjonalnie)
  - Cel: Copysight jako feeder do personal knowledge base, nie zamknięty silos

### UX pleasure principles (v9 — Minimalist Archive)

- **Empty state = the bare desk.** Manila surface with the URL slot recessed into it, the red button waiting. "COPYSIGHT" above. No text instructions — the affordance is physical.
- **Processing = the stamp show.** Large monospace stamps appearing one by one, full-screen, mechanical. Then dissolving into the Reader. The user watches the machine work.
- **Reading = absolute focus.** Screen 3 strips away everything. Just serif text on paper with wide margins. One small red date stamp. Nothing else competes for attention.
- **Library = accumulation.** The growing list of fiszki, each with a title, date, and color dot. Simple, scannable. The archive is a timeline of learning, not a dashboard.
- **Sidebar tabs = physical filing.** Flat colored rectangles, staggered like real folder tabs. They connect the digital archive to the analog filing cabinet metaphor without overdoing the skeuomorphism.

### Resolved design questions

- **Pivot from Lupek/Slate to Analog Archive (v7→v8).** Dark intelligence terminal aesthetic retired. New direction: warm skeuomorphism inspired by Austin Kleon's filing systems.

- **Pivot from heavy skeuomorphism to Minimalist Archive (v8→v9).** The 3×3 card grid retired. Screen 3 becomes a clean paper document with three editorial paragraphs. Screen 4 becomes a flat text list with search. Skeuomorphism concentrated on Screens 1-2 (input/processing) and stripped from Screens 3-4 (reading/archiving). Rationale: the reading experience demands calm and focus; the input experience benefits from tactile personality. The app transitions from "workshop" to "reading room."

- **Output as paragraphs, not cards (v8→v9).** The 3×3 card grid (v8) replaced by three flowing editorial paragraphs. Practical Insights, Observant Analysis, Predictions — each a complete, readable paragraph with bold inline header. One reading flow from start to finish. The editorial magazine feel is achieved through typography and whitespace, not through card borders.

- **Typography locked (v9).** IBM Plex Sans (headers/branding), Charter/Georgia (reading), IBM Plex Mono (status/metadata). No more candidates to evaluate — these are the production fonts.

- **Name resolved: Copysight.** Copy (journalistic clipping, editorial content) + Sight (insight, foresight, oversight). Previous working name Clipsight retired.

- **Workflow resolved (v9).** One-click pipeline: red button triggers Download → Transcribe → Analyze → auto-display. No intermediate decisions. Transcription saved as local file only, not visible in UI. Screen transitions: auto from Screen 2→3, manual swipe/arrow between Screen 3↔4.

- **Sidebar tabs resolved (v9).** Age-based filing system: Fresh (7d, black), Recent (30d, blue), Settled (6mo, red), Gold (6mo+, gold). Automatic — fiszki move between tabs as they age. Previous placeholder names (Library, Archive, Doom Clippings, Gold) retired.

- **Category dots removed (v9).** Library list is clean text: Title + Date. The age-based sidebar tabs provide all the visual structure needed. Dots were visual noise in a minimalist view.

- **Gear aesthetic resolved (v9).** Gears are watercolor stains on paper — static, blurred, warm brown (`#B8A070`), soaked into the surface like aged stamp prints. NOT mechanical, NOT animated. They're decorative watermarks, not moving parts. Present on Screens 1-3 for visual continuity, absent from Screen 4 (Library is clean text).

### Open design questions

- **Charter vs Georgia — do prototypu.** Both are elegant serifs. Charter is more editorial, Georgia more universal. Final choice after prototype testing with real AI output text.
