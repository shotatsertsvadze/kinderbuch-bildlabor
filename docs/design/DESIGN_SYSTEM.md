# Design System: Studio

Design specification for the Kinderbuch-Bildlabor user interface. The concept is the
**digitization studio** where these scans are made: neutral studio gray (the standard surround for
judging color), crisp contemporary type, a vivid cobalt version of *Berliner Blau* reserved for the
next action, and one signature element: the review path drawn as a **calibration strip**, like the
color target photographed next to every library scan. The UI language stays German; this document
is written in English for the implementing agent.

- **Implementation prompts:** [GG_CODER_PROMPTS.md](GG_CODER_PROMPTS.md)
- **Implementation:** [`.streamlit/config.toml`](../../.streamlit/config.toml), [`theme.py`](../../src/kinderbuch_bildlabor/theme.py), [`workflow.css`](../../src/kinderbuch_bildlabor/workflow.css), fonts in [`static/fonts/`](../../static/fonts/)
- **Screenshots:** [docs/screenshots/](../screenshots/)

Phase 1 (tokens, fonts, light and dark themes, base CSS, calibration strip) was prototyped against
Streamlit 1.67.0 in an isolated copy of the app: all 191 tests passed unchanged, and `ruff check`,
`ruff format --check` and `mypy` were clean. The fonts loaded from local files with no network access.

![Start page](../screenshots/01-start.png)

---

## 1. Who uses this and what they do

Reviewers at a library or archive check historical children's-book illustrations against the
saved scan and the catalogue metadata. They confirm region frames, decide between conflicting
classifications, check descriptions and transcriptions, give a named final approval, and export
the result with provenance. Sessions are long, the work needs care, and every decision is signed
with a name. The interface has to support **careful, repeated looking at old images** and make
**review state readable at a glance**.

## 2. Direction

**Why not the reading-room look.** The first proposal ("Lesesaal": cream paper, serif headings)
read as old-fashioned. Cream plus a high-contrast serif is also one of the most common default
looks right now, so it does not give the tool its own identity. It also works against the task:
a warm surround shifts how sepia scans are perceived.

**Studio.** The tool's real-world counterpart is the digitization workstation: neutral gray
surfaces, calibrated light, rulers and color targets, labels on scan slips. That gives a modern,
precise look that is specific to this subject, and it helps the scans look right.

| Element | Choice | Why |
|---|---|---|
| Surfaces | Neutral studio gray `#F4F5F3`, white cards | Neutral surround for judging scans; calm and contemporary |
| Action color | Cobalt `#2448C9` ("Berliner Blau, digital") | Keeps the Berlin connection (Prussian blue was first made in Berlin) in a modern, vivid form |
| Display type | Bricolage Grotesque | Contemporary grotesque with ink traps and a hint of print warmth that suits children's books, used only for headings and large values |
| Text type | Geist | Crisp, neutral, highly legible UI face |
| Utility type | Geist Mono | Labels and identifiers, like the slip that travels with a scan |
| Signature | Prüfpfad as calibration strip | The steps really are a sequence; the strip shows each step's state as a patch |

## 3. Design principles

1. **The scan is the subject.** The image gets the most space and a neutral surround. No UI chrome
   competes with it, and it is never cropped by layout.
2. **One next action.** In any area of the screen there is at most one primary (cobalt) button,
   and it is the step the Prüfpfad recommends. Everything else is secondary or tertiary.
3. **State is always readable.** Every review state is shown as icon + word + color, never color
   alone, and the same state looks the same everywhere (sidebar, Prüfpfad, tab content, cards).
4. **Provenance is visible.** Machine-made content (Colibri automatic class, OCR, AI draft) is marked
   with one consistent "maschinell" style, distinct from human decisions.
5. **Calm density.** Explanations are available but not shouting: one-line captions, longer
   rationale in expanders or `help=` tooltips. Visual noise is reduced before content is removed.
6. **Offline and accessible by default.** No runtime CDN. WCAG 2.2 AA contrast, keyboard operable,
   reduced motion respected, German page language for screen readers.

## 4. What changes compared with today

| Area | Today | Change |
|---|---|---|
| Overall look | Beige paper, serif headings, left accent bars: reads as old-fashioned | Neutral studio gray, white cards, grotesque type, no accent bars |
| Typography | Streamlit defaults (Source Sans/Serif); keyboard hint renders in Arial | Bundled Bricolage Grotesque + Geist + Geist Mono; every text uses the theme fonts |
| Language | `<html lang="en">` on a German UI: screen readers mispronounce, no hyphenation | `lang="de"`; hyphenation of long compounds on phones |
| Inputs | Beige fields on beige page read as disabled; border contrast about 1.3:1 | White fields with a 3:1+ border (WCAG 1.4.11) |
| Captions | Muted with `opacity: 0.7` (also fades icons and links) | Fixed muted ink color, 5.8:1 or better |
| Status colors | Streamlit default yellow/blue/orange; "Offen" in orange, so a fresh object looks alarming | Harmonized semantic palette; untouched = neutral gray, amber only for saved-but-unconfirmed |
| Prüfpfad steps | Row of round pills, hard to tell done from upcoming | Calibration strip: equal segments, gray/green/cobalt state edge, check icon |
| Scan display | Warm paper surround | Neutral gray mat ("Passepartout") behind every scan |
| Region overlays | Same region is red on overview tabs (colored by number) and blue in the editor (colored by type) | One color per region type everywhere, color-blind-safe (Okabe-Ito) |
| Object page | Header, Prüfpfad card, two captions and the keyboard hint push the scan below the fold at 1440×900 | Compact Prüfpfad; explanations folded in; work area starts higher |
| Navigation | Sidebar radio list with no state | Sidebar list rows with active highlight and per-object state |
| Dark mode | None | "Studio bei Nacht" follows the OS setting |

## 5. Color

### 5.1 Core tokens

All text/background pairs were checked against WCAG 2.2 (ratios in brackets).

| Token | Role | Light | Dark |
|---|---|---|---|
| `canvas` | App background (Streamlit `backgroundColor`) | `#F4F5F3` | `#111315` |
| `surface` | Cards, inputs, expanders (Streamlit `secondaryBackgroundColor`) | `#FFFFFF` | `#1A1D20` |
| `sunken` | Sidebar, table header, inline code | `#EBEDEA` | `#23272B` |
| `border` | Decorative borders, dividers | `#DCDFDA` | `#30353A` |
| `border-strong` | Secondary button outlines | `#C3C8C1` | `#454B52` |
| `control` | Input field borders (needs 3:1) | `#878D86` (3.1–3.4:1) | `#7C838B` (4.4–4.9:1) |
| `ink` | Body text | `#15181C` (15.1–17.8:1) | `#E8EBED` (12.6–15.6:1) |
| `ink-muted` | Captions, labels, metadata | `#555B62` (5.8–6.9:1) | `#A2A9B1` (6.3–7.8:1) |
| `ink-subtle` | Placeholders, on `surface` only | `#6E747B` (4.7:1) | `#8A9199` (5.3:1) |
| `primary` | Cobalt: next action, focus, links | `#2448C9` (6.3–7.4:1) | `#94AAFF` (6.8–8.4:1) |
| `on-primary` | Label on primary buttons | `#FFFFFF` (7.4:1) | `#0B1640` (7.9:1) |
| `primary-tint` | Hover/selected background | `#E9EDFB` | `#1D2547` |
| `ok` | Done edge and icon | `#146C3A` | `#86D6A2` |
| `open` | Upcoming edge in the strip | `#C9CDC7` | `#3A4047` |
| `mat` | Neutral surround behind scans | `#E2E3E1` | `#0B0C0D` |

Streamlit derives the label color of primary buttons itself and puts white on the light dark-mode
cobalt (2.3:1). `workflow.css` therefore sets primary button labels to `on-primary`.

### 5.2 Semantic status colors

One vocabulary for every review state. These map onto Streamlit's named colors in `config.toml`,
so `st.success`, `st.warning`, `st.error`, `st.info` and `st.badge(color=…)` pick them up without
code changes.

| State (UI wording stays as is) | Meaning | Streamlit color | Icon | Light text / bg | Dark text / bg |
|---|---|---|---|---|---|
| **Offen** (untouched, proposed, provisional) | Nobody has worked on this yet | `gray` | `:material/radio_button_unchecked:` | `#4A5058` / `#ECEEEB` (7.0:1) | `#C9CED4` / `#2A2E33` (8.6:1) |
| **Entwurf / ungespeicherte Änderung** | Saved or typed, not yet confirmed | `yellow` and `orange` (same amber) | `:material/edit_note:` | `#8A5300` / `#FDF0D5` (5.6:1) | `#F5C26B` / `#3A2A10` (8.4:1) |
| **Bestätigt** | Named person confirmed this area | `green` | `:material/check_circle:` | `#146C3A` / `#E3F3E8` (5.6:1) | `#86D6A2` / `#16301F` (8.2:1) |
| **Endbestätigt** | Final approval given (not Ground Truth) | `green` | `:material/verified:` | as Bestätigt | as Bestätigt |
| **Blocker, Konflikt, Fehler** | Must be resolved; blocks approval | `red` | `:material/block:` / `sync_problem` / `error` | `#B3261E` / `#FCE8E6` (5.6:1) | `#FFA59C` / `#3F1C19` (8.0:1) |
| **Hinweis, nicht ausgeführt** | Neutral system information | `blue` (slate, not cobalt) | `:material/info:` | `#3B5268` / `#E8EEF3` (6.9:1) | `#A9C3DB` / `#1C2A37` (8.0:1) |
| **Maschinell** (Colibri automatisch, OCR, KI-Entwurf) | Provenance marker | `violet` | `:material/smart_toy:` | `#6A3DB8` / `#F1EAFD` (6.0:1) | `#C7B0FF` / `#2A2142` (8.0:1) |
| **Nächste Handlung** | Call to action | `primary` button | `:material/arrow_forward:` | white on `#2448C9` | `#0B1640` on `#94AAFF` |

Rules:

- Amber means "work was done here that still needs a named confirmation". It is not used for
  untouched items. A fresh object should look calm (gray), not alarming.
- Red is reserved for things that block approval or need intervention.
- Cobalt is never used for status; it only marks the action to take.

### 5.3 Region overlay colors (on scans)

Overlays sit on warm, high-texture woodcuts, so they use the color-blind-safe Okabe-Ito hues plus
the existing white outer halo and dark inner line (keep that technique from `regions.py`).

| Region type | Color | Notes |
|---|---|---|
| Illustration | `#0072B2` (blue) | Default for image regions |
| Text | `#D55E00` (vermilion) | Transcription regions |
| Other / unknown | `#009E73` (bluish green) | Fallback |
| Unsaved new region | Type color, dashed `2u 1.5u` | Dash pattern, not color, signals "not saved" |
| Selected | Type color, stroke ×1.5, white corner handles | |

Color by **type**, not by region number, in both the server-rendered crops (`regions.py`) and the
canvas editor (`region_canvas.js`). The number label stays as the identifier.

## 6. Typography

### 6.1 Families (all SIL Open Font License, bundled locally)

| Role | Family | Use | Files (Fontsource 5.3.0) |
|---|---|---|---|
| Display | **Bricolage Grotesque** (variable, weight + optical size) | Headings, hero title, large comparison values. Nothing else. | `bricolage-grotesque-latin-opsz-normal.woff2`, `…-latin-ext-opsz-normal.woff2` |
| Text and UI | **Geist** (variable weight) | Body, labels, buttons, captions, research question | `geist-latin-wght-normal.woff2`, `…-latin-ext-wght-normal.woff2` |
| Utility | **Geist Mono** (variable weight) | Eyebrow labels, PPN, `DMDLOG_0000`, coordinates `[229, 299, 924, 617]`, checksums, paths | `geist-mono-latin-wght-normal.woff2`, `…-latin-ext-wght-normal.woff2` |

Total payload is about 200 KB, served from `static/fonts/` via `server.enableStaticServing`.
Include each package's `LICENSE` next to the fonts (`static/fonts/OFL-<family>.txt`). Geist has no
italic; do not use italics for emphasis (use weight 500–600).

### 6.2 Scale

| Use | Font | Size / line height | Weight / tracking |
|---|---|---|---|
| Hero title (start page only) | Bricolage | `clamp(2.5rem, 5vw, 4rem)` / 0.98 | 700 / −0.035em |
| h1 object title | Bricolage | 2.5rem / 1.1 | 650 / −0.022em |
| h2 section | Bricolage | 1.625rem / 1.2 | 600 / −0.022em |
| h3 subsection | Bricolage | 1.25rem / 1.25 | 600 |
| Comparison value (st.metric) | Bricolage | 2.25rem (Streamlit default size) | 600 / −0.02em |
| Research question (Leitfrage) | Geist | 1.25rem / 1.45, max 40ch | 500 |
| Body | Geist | 1rem (16px) / 1.6 | 400 |
| Label, button | Geist | 0.875–1rem | 500 (current step 600) |
| Caption | Geist | 0.875rem / 1.5, color `ink-muted` | 400 |
| Eyebrow (PRÜFPFAD · SCHRITT 1 VON 5) | Geist Mono | 0.75rem, uppercase (from the copy) | 500 / 0.04em |
| Identifier | Geist Mono | 0.875em | 400 |

### 6.3 German typography rules

- `lang="de"` on `<html>` (Streamlit ships `lang="en"`). Hyphenation (`hyphens: auto`) only below
  641px width, where long compounds such as *Endbestätigung* would otherwise overflow; on wide
  screens words stay whole, so quoted class names like „Abbildung“ are never split.
- Keep German quotation marks „…“ exactly as written in the copy.
- `font-variant-numeric: tabular-nums` for counters ("0 von 4 bestätigt"), progress text and tables.
- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs.
- Line length for running text: 60–80 characters; do not stretch paragraphs across the full layout.

## 7. Spacing, shape, elevation

- **Spacing scale (rem):** 0.25 · 0.5 · 0.75 · 1 · 1.5 · 2 · 3 · 4. Use 1.5rem between related
  blocks, 3rem between page sections.
- **Radius:** inputs and buttons 0.625rem; strip and expanders 0.75rem; scan mat 0.875rem; cards
  1rem; scan images 0.25rem (paper has nearly square corners).
- **Elevation:** `shadow-1` (a 1–2px soft shadow) for cards; scans use `shadow-scan`. No other
  shadows. Prefer borders over shadows.
- **Touch targets:** at least 40px high on desktop, 44px on phones (strip segments are 52px).

## 8. Layout and information architecture

### 8.1 App shell

```
┌ Sidebar (sunken) ─────────┐ ┌ Main (canvas) ─────────────────────────────────────────────┐
│ Kinderbuch-Bildlabor       │ │ Genovefa · Scan 22                                          │
│                            │ │ Schmid, Christoph, von · Augsburg 1810 · … · PPN1772789429  │
│ Start und Sammlung         │ │ ┌ Prüfpfad (white card) ────────────────────────────────────┐ │
│ Eigenes Buch importieren   │ │ │ PRÜFPFAD · SCHRITT 2 VON 5 · …     Prüfende Person [____]  │ │
│ 1 · Heimath, Scan 6        │ │ │ Nächste Handlung: …                                        │ │
│   offen                    │ │ │ ▬▬▬▬▬▬░░░░░░░░ 1 von 4 bestätigt · 0 Entwurf · 3 offen    │ │
│ 2 · Genovefa, Scan 14      │ │ │ ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │ │
│   1 von 4 bestätigt        │ │ │ │▀▀green▀▀▀│██cobalt██│▀▀gray▀▀▀▀│▀▀gray▀▀▀▀│▀▀gray▀▀▀▀│  │ │
│▌5 · Genovefa, Scan 22      │ │ │ │✓ 1 Bild  │2 Klassen │3 Beschr. │4 Abschl. │5 Export  │  │ │
│   1 von 4 bestätigt        │ │ │ └──────────┴──────────┴──────────┴──────────┴──────────┘  │ │
│                            │ │ └────────────────────────────────────────────────────────────┘ │
│ Eingaben werden erst mit … │ │ Übersicht | Klassifikation | Regionen | … | Prüfung | Export │
└────────────────────────────┘ │ ┌ Scan on gray mat (sticky) ┐ ┌ Work panel ───────────────┐  │
                               │ │        [ scan ]            │ │ question · form · sign-off│  │
                               │ └────────────────────────────┘ └───────────────────────────┘  │
                               └─────────────────────────────────────────────────────────────┘
```

- **Sidebar:** wordmark in Bricolage; navigation as list rows; the active row sits on `surface`
  with a 3px inset cobalt edge; under each object a short state line (Phase 2).
- **Object header:** H1 "Genovefa · Scan 22" in Bricolage, metadata line in `ink-muted`.
- **Prüfpfad:** one white card. The two captions that currently sit below it (step explanation
  and keyboard hint) move inside the card, into its footer or the "Prüfbereiche dieses Objekts"
  expander. Goal at 1440×900: the tab bar and the top of the scan are visible without scrolling.
- **Work area:** two columns, scan left (2) and controls right (3), as today (`ui.SPLIT`). The scan
  column stays sticky on wide screens.

### 8.2 Start page order

Keep the demo narrative but bring the collection closer to the top:

1. Hero: mono eyebrow, Bricolage title, research question, short intro, primary "Leitbeispiel
   öffnen" and "Eigenes Buch importieren" as a secondary button next to it (move it out of the
   floating position above the hero); illustration on the gray mat.
2. Stichprobe grid: six object cards with status badge, progress and Colibri classes (manual as
   gray badge, automatic as violet "maschinell" badge).
3. Fallstudie table.
4. Abgeschlossenes Beispiel.
5. Zweites Beispiel.
6. Begriffe kurz erklärt.
7. Werkzeuge: CSV export and Sicherung side by side.

## 9. Components

| Component | Spec |
|---|---|
| **Calibration strip** (signature; Prüfpfad step buttons in `st.container(key="guide-steps")`) | One continuous strip, 1px `border`, radius 0.75rem, segments of equal width (min 8.5rem, wraps on phones), 52px high, no gaps. Each segment has a 4px top edge: `open` gray for upcoming, `ok` green plus check icon for done, and the current step is a solid cobalt segment with `on-primary` label. Hover on other segments: `primary-tint`. No bounce animation inside the strip. Keep keys and `help=` texts. |
| **Primary button** | Cobalt fill, `on-primary` label, radius 0.625rem, optional leading arrow icon. One per area. The two-bounce "next step" nudge stays on "Leitbeispiel öffnen" and "Weiter"; off under reduced motion. |
| **Secondary button** | White, 1px `border-strong`, ink label. |
| **Tertiary / link** | "Scan in der Originalansicht öffnen": link style with external-link icon. |
| **Eyebrow** | Geist Mono 0.75rem, `ink-muted`, in keyed containers `guide-eyebrow` and `hero-eyebrow`. |
| **Status badge** | `st.badge` with the semantic color and icon from 5.2. Wording unchanged. |
| **Sign-off panel** (`ui.confirm_controls`, key `…-review-box`) | Reads as a signature block: `surface`, 1px `border-strong`, radius 0.75rem; statement checkbox; primary confirm button; lock icon + reason in `ink-muted` when disabled. |
| **Decision options** (radios with keys ending `-outcome`) | Each option a full-width row: 44px min height, 1px border, radius 0.625rem; hover border `primary`; selected = `primary` border + `primary-tint`. The sidebar radio is not affected. |
| **Comparison cards** ("Colibri manuell" vs "Colibri automatisch") | Two equal `st.metric` cards; value in Bricolage; the automatic card gets a violet "maschinell" badge. |
| **Scan stage** | `mat` background, 0.875rem padding and radius; image radius 0.25rem with `shadow-scan`; caption below in `ink-muted`. |
| **Alerts** | Theme colors from 5.2 plus a 1px border at 20% of the text color, radius 0.75rem. Avoid stacking more than one alert per area. |
| **Tabs** | Weight 500, active 600 with cobalt underline. Optional: sticky tab bar (adjust the sticky scan offset). |
| **Tables** | Header on `sunken`, tabular numbers, 1px `border`. |
| **Keyboard hint** (`review_keys.py`) | Inherit the theme font; 0.875rem; color `var(--bl-ink-muted)`. |
| **Focus** | 3px `primary` outline, 2px offset (inside the strip: −3px), on every interactive element. |

## 10. Motion

Only two motions: the "next step" nudge (700ms, twice) on "Leitbeispiel öffnen" and "Weiter", and
hover color changes. Everything is disabled under `prefers-reduced-motion: reduce`.

## 11. Accessibility checklist

- [ ] Text contrast ≥ 4.5:1, large text ≥ 3:1, input borders and focus ring ≥ 3:1 (values in §5
  already pass in both modes).
- [ ] Primary button labels use `on-primary` in both modes.
- [ ] No state conveyed by color alone (icon + word always present; the strip's done segments carry
  a check icon).
- [ ] `lang="de"` set on the document.
- [ ] All actions reachable by keyboard; visible focus ring everywhere; keyboard hint readable.
- [ ] Usable at 200% browser zoom and at 390px width without horizontal scrolling.
- [ ] Images keep their `alt` texts.
- [ ] Reduced motion respected.

## 12. Implementation notes for Streamlit 1.67

- **Configuration first, CSS second.** Colors, fonts, heading sizes, radius and dark mode are native
  `config.toml` options in 1.67 (`[theme.light]`, `[theme.dark]`, `[[theme.fontFaces]]`,
  `headingFontSizes`, `greenBackgroundColor`, …). The implementation is
  [`.streamlit/config.toml`](../../.streamlit/config.toml).
- **Tokens for custom CSS** come from `theme.inject()` ([`theme.py`](../../src/kinderbuch_bildlabor/theme.py)),
  which writes `--bl-*` CSS variables for the active mode using `st.context.theme.type` and sets
  `lang="de"`. `workflow.css` uses only these variables, never raw hex values.
- **Selectors:** prefer the `.st-key-<key>` classes Streamlit adds to keyed containers. The design
  needs three new hooks: `guide-steps` (strip), `guide-eyebrow`, `hero-eyebrow`. Use `data-testid`
  selectors sparingly, never `:nth-child`, and never `:first-child` on generic elements (in the
  prototype a `:first-child` caption rule leaked onto unrelated captions).
- **Do not change** widget keys, tab labels, session-state keys, German copy, or the element type of
  any text (`st.caption`, `st.markdown`, `st.info`, `st.success`, `st.warning`, `st.error`,
  `st.subheader`, `st.title`). The tests assert exact texts per element type. Restyle through the
  theme instead.
- **Offline:** no Google Fonts or CDN URLs at runtime. Fonts live in `static/fonts/`.
- **Font download** (one time; or copy from `npm pack`):
  `https://cdn.jsdelivr.net/npm/@fontsource-variable/bricolage-grotesque@5.3.0/files/<file>`,
  `https://cdn.jsdelivr.net/npm/@fontsource-variable/geist@5.3.0/files/<file>`,
  `https://cdn.jsdelivr.net/npm/@fontsource-variable/geist-mono@5.3.0/files/<file>`;
  license files at `…/<package>@5.3.0/LICENSE`.
- **Verify visually** only with an isolated data directory:
  `BILDLABOR_DATA_DIR=$(mktemp -d) uv run streamlit run app.py`.
  Opening the app can migrate and write working copies.

## 13. Implementation status

All five phases are implemented. The reference files that were used to apply Phase 1 have been
removed; the live files listed at the top are the source of truth.

| Phase | Content | Status |
|---|---|---|
| 1 | Tokens, bundled fonts, light and dark themes, base CSS, calibration strip | Implemented |
| 2 | Compact Prüfpfad card, sidebar state per object | Implemented |
| 3 | Status badges and colors, "maschinell" marker, decision option rows, sign-off panel, scan mat | Implemented |
| 4 | Region overlay colors by type (Okabe-Ito) in overlays and canvas editor | Implemented |
| 5 | Start page order, import next to the lead action, card badges, side-by-side tools | Implemented |

Known gaps against this document:

- An untouched decision shows the amber `st.warning` "Offen: Antwort wählen, …" instead of gray,
  because the element type may not change.
- Section headings (`st.subheader`) render as `h3` below the `h1` title. `theme.inject()` sets
  `aria-level="2"` on them in the browser, so the heading order is valid without changing the
  element type or the look.
- The start page shows the first row of object cards after one scroll; the second row needs a
  further scroll.

Screenshots of the current state are in [docs/screenshots/](../screenshots/).
