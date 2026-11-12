# Prompts for the redesign (GG Coder)

Copy-ready prompts that implement [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) in six small, reviewable
phases. Each phase is one commit and leaves the app working.

## How to use

1. Make sure GG Coder works in a checkout that contains `docs/design/` (this folder).
2. Paste **Prompt 0** at the start of every new GG Coder session. It sets the rules.
3. Paste **one** phase prompt. Review the result (screenshots, test output) before the next phase.
4. If a phase reports a failing test, do not let it "fix" the test by changing assertions unless the
   prompt says so. Ask for the cause instead.

| Phase | What changes | Risk | Effort |
|---|---|---|---|
| 1 Foundation | Fonts, colors, light/dark theme, base CSS, calibration strip | Low (validated: 191/191 tests pass) | S |
| 2 Orientation | Compact Prüfpfad, sidebar status | Low–medium | M |
| 3 Review workspace | Status colors, sign-off panel, decision options, comparison cards | Medium | M |
| 4 Region overlays | One color per region type in crops and editor | Medium (one test changes) | S |
| 5 Start page | Section order, collection cards, tools section | Low–medium | M |
| 6 QA pass | Accessibility, responsive checks, screenshot refresh | Low | S |

---

## Prompt 0: Context and rules (paste first, every session)

```text
You are working on Kinderbuch-Bildlabor, a local, offline, German-language Streamlit 1.67 app for
reviewing historical children's-book illustrations. We are doing a presentation-only redesign
defined in docs/design/DESIGN_SYSTEM.md. Read that file and AGENTS.md before you change anything.

Hard rules for every task:
1. Presentation only. Do not change logic in review.py, store.py, validate.py, export.py,
   actions.py, oai.py, imports.py, import_transport.py, backup.py, ocr.py. You may read them.
2. Do not change any widget key, tab label, session_state key, or German UI wording.
3. Do not change the element type of any existing text (st.caption, st.markdown, st.text, st.title,
   st.subheader, st.info, st.success, st.warning, st.error). Tests assert exact texts per element
   type. Change appearance through .streamlit/config.toml and workflow.css instead.
   Adding new decorative elements (badges, keyed containers) is allowed.
4. Status must always be icon + word, never color alone.
5. Offline: no CDN, Google Fonts or other runtime network URLs. Fonts are bundled in static/fonts/.
6. CSS: use only --bl-* variables from theme.py, never raw hex values in workflow.css. Prefer
   .st-key-<key> selectors; add st.container(key="...") hooks when needed. Never use :nth-child
   or :first-child on Streamlit's generic elements.
7. Never open the app on real working data. For any manual or browser check, start it with a fresh
   temporary data directory:
     BILDLABOR_DATA_DIR="$(mktemp -d)" uv run streamlit run app.py
   (Windows PowerShell: $env:BILDLABOR_DATA_DIR = New-Item -ItemType Directory -Path "$env:TEMP\bl-$(Get-Random)"; uv run streamlit run app.py)
8. Do not commit data/, exports/, backups, credentials, or screenshots containing real review data.
   Do not edit uv.lock. If "uv run --locked" fails because your uv is older than the lockfile,
   update uv instead of re-locking.
9. Before you finish any task, run and report the output of:
     uv run --locked ruff check --no-cache .
     uv run --locked ruff format --check --no-cache .
     uv run --locked mypy
     uv run --locked python -B -m pytest -p no:cacheprovider -q
   All must pass. If a test fails, stop and explain the cause; do not edit tests unless the task
   explicitly allows it.
10. If you can run a headless browser (Playwright), take screenshots at 1440x900 and 390x844 of the
    start page and of "Genovefa, Scan 22" (tabs Regionen, Klassifikation, Prüfung) in light and dark
    color scheme, and show them to me. Otherwise list what I should check by hand.
11. End with a short summary: files changed, what I should look at, anything you were unsure about.
    Make one commit per task with a clear English message.

Reply "Ready" when you have read DESIGN_SYSTEM.md and AGENTS.md.
```

---

## Prompt 1: Foundation (fonts, colors, light and dark theme, calibration strip)

```text
Task: Phase 1 of docs/design/DESIGN_SYSTEM.md ("Studio"). Install the design tokens, bundled fonts,
light and dark themes, the base stylesheet and the calibration-strip Prüfpfad. The reference files
in docs/design/reference/ were already validated against this codebase (all tests, ruff and mypy
pass); apply them rather than reinventing them.

Steps:
1. Fonts. Create static/fonts/ at the repository root (next to app.py) with exactly these files,
   version 5.3.0 from Fontsource (download from https://cdn.jsdelivr.net/npm/<package>@5.3.0/files/<file>,
   or run "npm pack <package>@5.3.0" and copy from package/files/):
     @fontsource-variable/bricolage-grotesque: bricolage-grotesque-latin-opsz-normal.woff2,
                                              bricolage-grotesque-latin-ext-opsz-normal.woff2
     @fontsource-variable/geist:              geist-latin-wght-normal.woff2,
                                              geist-latin-ext-wght-normal.woff2
     @fontsource-variable/geist-mono:         geist-mono-latin-wght-normal.woff2,
                                              geist-mono-latin-ext-wght-normal.woff2
   Also save each package's LICENSE as static/fonts/OFL-Bricolage-Grotesque.txt, OFL-Geist.txt,
   OFL-Geist-Mono.txt (SIL Open Font License; required when redistributing).
2. Replace .streamlit/config.toml with docs/design/reference/config.toml. Keep every non-theme
   setting it already contains (address, showEmailPrompt, gatherUsageStats, toolbarMode); it adds
   server.enableStaticServing = true for the fonts.
3. Create src/kinderbuch_bildlabor/theme.py from docs/design/reference/theme.py (update its
   docstring path note).
4. In app.py, directly after st.set_page_config(...), call theme.inject() and keep the existing
   st.html(... "workflow.css") line after it. Add theme to the import list.
5. Replace src/kinderbuch_bildlabor/workflow.css with docs/design/reference/workflow.css.
6. In src/kinderbuch_bildlabor/review_keys.py, change only the inline style of the help paragraph
   from "margin:0;font:14px sans-serif;color:#555" to
   "margin:0;font:inherit;font-size:0.875rem;line-height:1.5;color:var(--bl-ink-muted, #555B62)".
7. Add the three style hooks the stylesheet expects (same texts, same element types, same keys
   inside them):
   - workflow.render: the step button row becomes
     st.container(horizontal=True, gap="xsmall", key="guide-steps").
   - workflow.render: wrap st.caption(f"PRÜFPFAD · …") in st.container(key="guide-eyebrow").
   - collection_view.hero: wrap st.caption("BILDARCHIV · FALLSTUDIE") in
     st.container(key="hero-eyebrow").
8. README.md: in "Weitere Dokumente", add a link "[Gestaltung](docs/design/DESIGN_SYSTEM.md)".
   Mention in one German sentence under "Daten" or a fitting place that fonts are bundled under
   static/fonts/ (SIL OFL). Keep the README's tone and language.

Done when:
- In the browser, document.fonts lists Bricolage Grotesque, Geist and Geist Mono as loaded, the
  network tab shows the .woff2 files served from /app/static/fonts/, and <html lang="de">.
- Headings use Bricolage Grotesque, body uses Geist, eyebrows and inline code use Geist Mono.
- The Prüfpfad steps form one continuous strip: gray top edge for upcoming steps, green edge and
  check icon for done steps, a solid cobalt segment for the current step.
- Inputs are white with a clearly visible border; captions are a solid muted color.
- With the OS in dark mode the app uses the dark studio theme; primary buttons there have a dark
  label on light cobalt (not white).
- No paper/beige tones and no serif fonts remain.
- All four quality checks pass.
```

---

## Prompt 2: Orientation (Prüfpfad, sidebar)

```text
Task: Phase 2 of docs/design/DESIGN_SYSTEM.md (section 8.1).
Goal: at 1440x900 on "Genovefa, Scan 22", the tab bar and the top of the scan are visible without
scrolling, and the sidebar shows each object's review state.

Steps:
1. Compact Prüfpfad. Move the step explanation caption ("Die Schaltflächen des Prüfpfads …") from
   below the card into the card, inside the "Prüfbereiche dieses Objekts" expander, after the
   existing caption there. Render the keyboard hint (review_keys.render) inside the card as its last
   row instead of below it; the simplest way is to let workflow.render accept a callable for the
   footer, or return the container. Keep st.progress and its text unchanged (tests read it).
2. Calibration strip on phones: at 390px width the strip wraps into rows; make sure every segment
   stays at least 44px high, the labels do not truncate, and the strip's outer border still reads
   as one block. Adjust only .st-key-guide-steps rules.
3. Sidebar status. In app.py sidebar(), keep st.radio with key="view" and the same option values.
   Group visually with two small headers above and inside the list if feasible; at minimum:
   - add the radio "captions" argument with a short German state per option:
     Start/Import: "" ; objects: "endbestätigt" if workflow.approved(record), otherwise
     "{bestätigt} von {gesamt} bestätigt" using workflow.area_counts(review.review_areas(record)),
     or "offen" when nothing is confirmed and no draft exists.
   - optionally prefix object labels in view_label with a Material icon
     (:material/radio_button_unchecked: offen, :material/clock_loader_40: in Arbeit,
     :material/verified: endbestätigt). Check that the icon renders as an icon, not as text; if it
     does not, leave the icon out (the caption already carries the state).
   - keep the list-row styling from Phase 1 (active row on surface with 3px inset cobalt edge);
     the radio circle stays present for keyboard and screen readers.
4. Remove the 4px left accent border from any card if still present (Phase 1 already does this for
   the hero and Prüfpfad).

Do not change: button keys (guide-*), tabs key, help texts, wording, st.progress text.
Done when: the screenshot at 1440x900 shows the tab bar above the fold, the sidebar shows a state
line under every object, and all quality checks pass.
```

---

## Prompt 3: Review workspace (status, sign-off, decisions, comparison)

```text
Task: Phase 3 of docs/design/DESIGN_SYSTEM.md (sections 5.2 and 9).

Steps:
1. Status badges (ui.status_badge): keep the text exactly. Map colors and icons:
   - status in review.DONE_STATUSES          -> color "green", icon :material/check_circle:
   - status in {review.KEYWORDS_EDITED, review.BIBLIO_EDITED} (saved, waiting for confirmation)
                                              -> color "orange" (amber in the theme), icon :material/edit_note:
   - every other open status                  -> color "gray", icon :material/radio_button_unchecked:
   Add the icon constants DRAFT, OPEN, FINAL (:material/verified:) next to the existing ones in ui.py.
2. Provenance: in ui.origin_note, show the caption in violet:
   st.caption(f":violet[:material/smart_toy: Herkunft: {origin}]"). Confirm the test that looks for
   "Entwurf des KI-Assistenten" in captions still passes.
3. Comparison cards (decision_view, the two st.metric cards): under the "Colibri automatisch"
   metric add st.badge("maschinell", icon=":material/smart_toy:", color="violet"). (The metric
   value already uses Bricolage Grotesque from Phase 1.)
4. Decision options: the radios in decision_view.decision_form have keys ending in "-outcome".
   Style [class*="-outcome"] [data-testid="stRadioOption"] as full-width option rows per §9
   "Decision options" (min-height 44px, border, radius, hover, selected state via
   :has(input:checked)). Make sure the sidebar radio is not affected.
5. Sign-off panel: ui.confirm_controls renders st.container(key=f"{key}-box") where key ends in
   "-review". Style [class*="-review-box"] per §9 "Sign-off panel".
6. Scan stage: confirm every scan shown next to controls (ui.image_and_controls with pinned=...)
   sits on the neutral mat. Also give the unpinned left column in overview_tab the same mat by
   adding a keyed container (e.g. key="scan-overview") and including it in the mat selector.
7. Alerts: keep element types. Only check that the theme colors from Phase 1 apply and that no
   area shows more than one alert stacked directly on another; if one does, list it for me
   instead of changing it.

Done when: a fresh object shows calm gray "Offen" badges, saved-but-unconfirmed areas show amber,
confirmed areas green; decision options are easy click targets; the automatic class is visibly
marked "maschinell"; all quality checks pass.
```

---

## Prompt 4: Region overlays (one color per type)

```text
Task: Phase 4 of docs/design/DESIGN_SYSTEM.md (section 5.3). Today the same region is drawn red on
overview tabs (regions.py colors by region number) and blue in the editor (region_canvas.js colors
by type). Make both color by region type with the Okabe-Ito palette.

Steps:
1. regions.py: replace COLORS with TYPE_COLORS = {"illustration": "#0072B2", "text": "#D55E00"} and
   OTHER_COLOR = "#009E73". In draw_regions use TYPE_COLORS.get(region.get("type"), OTHER_COLOR).
   Keep the white outer halo, the dark inner line and the number label exactly as they are.
2. region_canvas.js: use the same three colors for type strokes and the fallback, the dashed
   draft rectangle in the type color of the region being drawn (or the illustration color when
   unknown), and replace "#555", "#eee" and the "#1f77b4" mode-button outline with values that
   inherit the theme (e.g. var(--bl-ink-muted), var(--bl-mat), var(--bl-primary) with the current
   hex as fallback). Pass the color map from Python (region_canvas.py) to the component data so
   the two files cannot drift apart.
3. tests/test_regions.py: the pixel assertion compares against regions.COLORS[0]. Update only that
   reference to the new constant for the region's type. Do not loosen the assertion.

Done when: on "Genovefa, Scan 22" the illustration frame has the same blue on the Übersicht,
Klassifikation and Regionen tabs and in the editor; text regions on "Die Heimath in Amerika,
Scan 6" are vermilion everywhere; all quality checks pass.
```

---

## Prompt 5: Start page (order, cards, tools)

```text
Task: Phase 5 of docs/design/DESIGN_SYSTEM.md (section 8.2).

Steps:
1. In collection_view.render, reorder the sections to: hero, Stichprobe grid, Fallstudie table,
   Abgeschlossenes Beispiel (example_view.render), Zweites Beispiel, Begriffe, Werkzeuge.
   Keep every function, key and text; only the call order and grouping change.
2. Move the "Eigenes Buch importieren" button (key="import-start") into the hero, next to the
   "Leitbeispiel öffnen" button, as a secondary button in a horizontal container.
3. Collection cards (collection_view.card): above the image add a status badge using the same
   mapping as the sidebar (endbestätigt / in Arbeit / offen with the Phase 3 icons). Show the two
   Colibri classes as badges (manual: gray, automatic: violet "maschinell") in addition to the
   existing caption, not instead of it. Keep "Objekt öffnen" as a full-width secondary button.
4. Werkzeuge: put collection_export and backup_view.render side by side in two columns on wide
   screens (stacked on phones), each in a bordered container, under the subheader produced by
   their existing code.
5. Check the phone layout (390px): hero title must not overflow, the image follows the text.

Done when: the six object cards are visible after one scroll from the top on a 1440x900 screen,
import sits next to the lead action, and all quality checks pass.
```

---

## Prompt 6: QA pass (accessibility, responsive, documentation screenshots)

```text
Task: Final quality pass for the redesign in docs/design/DESIGN_SYSTEM.md.

1. Run the accessibility checklist in DESIGN_SYSTEM.md §11. If Playwright is available, also run
   axe-core (inject https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js only in the test
   browser, never in the app) on the start page and the Regionen, Klassifikation and Prüfung tabs
   of "Genovefa, Scan 22", in light and dark. Report violations with selector and fix the ones
   caused by our CSS or theme.
2. Keyboard: Tab through the object page. Every control shows the focus ring; the keys n, b and ?
   still work (see review_keys.py).
3. Zoom 200% and width 390px: no horizontal scrolling; the sticky scan does not cover controls.
4. Search workflow.css and theme.py for any raw hex value outside theme.py TOKENS and fix it.
5. Refresh the screenshots in docs/screenshots/ (same file names, same views as today) from an
   isolated data directory. Make sure they contain no real reviewer names beyond what the
   bundled example already shows.
6. Update docs/design/DESIGN_SYSTEM.md §13 to say which phases are implemented, and delete
   docs/design/reference/ once its contents live in the real files (mention this in the commit).

Report: a table of checks with pass/fail and what you changed.
```

---

## Optional follow-ups (ask separately if wanted)

- **Sticky tab bar** below the header so reviewers always see where they are on long tabs. Needs
  the sticky scan offset adjusted (`top` in workflow.css).
- **Object header eyebrow** ("SAMMLUNG · GENOVEFA · AUGSBURG 1810") and PPN in mono. Only if no test
  asserts on the current caption text.
- **Segmented progress** (bestätigt / Entwurf / offen in three colors) as a decorative `st.html` bar
  next to the existing `st.progress`, not replacing it.
