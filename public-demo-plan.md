# Public read-only demo: implementation plan (for approval)

Status: approved 2026-11-15 (options 1/1/1); steps 1-3 implemented. Step 4: the owner's review session
(Scan 22 only) passes `demo_data check`; a snapshot was built outside the repository and waits for the
licence entries. Step 6: Dockerfile, deploy/ and rechtliches/ written 2026-11-20 and run as a read-only
local stand-in (no Docker on the build machine, so the image itself is not yet built). 2026-11-21: the
full visitor walk also ran through the real `deploy/Caddyfile` (local Caddy 2.11.9), the Dockerfile steps
were replayed in TZ=UTC (uv.lock timezone fix in pyproject.toml), and both publication gates were shown
to block and to pass. Step 7 needs the owner's purchase decision. Steps 5 and 8 not started.
Step 3 deviation (by request): editing controls are hidden in demo mode, not shown disabled.
Since step 3, import, similarity search, backup and the docs/ergebnis example are not shown in demo
mode; the backend refusals from step 2 remain.
Strict export validation (exact match) chosen. Original status: plan only. No application code, data, hosting or deployment has been changed for this plan.
Approved direction: (1) fix export consistency first, (2) read-only demo switch in the same app with backend
write guard and read-only container, (3) Hetzner EU VPS with Docker and Caddy, (4) the owner's full name
consistently, test identities removed, (5) curated `demo/` folder committed with checksums, exception noted
in AGENTS.md.

Evidence labels: RUNTIME = executed and observed; CODE = read in source; DEDUCED = inferred.

## 0. Facts this plan relies on

| Fact | Evidence |
|---|---|
| Viewing start page and an object writes nothing to the data folder (0 files) | RUNTIME, isolated `BILDLABOR_DATA_DIR`, 2026-11-15 |
| One server process with one browser session: physical footprint 175 MB, peak 180 MB (macOS) | RUNTIME; Linux container numbers must be re-measured in step 6 |
| Installed environment 426 MB incl. dev tools; largest runtime packages pyarrow 126 MB, pandas 53 MB, streamlit 38 MB | RUNTIME (`du`) |
| Rendering an object probes Ollama on localhost (`object_view.py:219` -> `proposals.available`, 0.5 s timeout) | CODE |
| Rendering the OCR expander runs `tesseract --list-langs` (`object_view.py:878` -> `ocr.listing`) | CODE |
| Loading an older-format working copy saves a migration (`store.py:231-232`) | CODE |
| After a mid-way export write failure with an earlier export present, files from two exports coexist and the panel still says "Export aktuell"; the notice disappears on the next rerun | RUNTIME (scratch test, deleted) |
| `run_export` does not hold `store.LOCK` | CODE (`actions.py:415`) |
| GitHub repository is PUBLIC; tracked `docs/ergebnis/genovefa-scan-022.json` contains reviewer names "Shota Tsertsvadze" (9), "shota" (6), "ShotaTest" (3) | RUNTIME (`gh repo view`, `grep`) |
| All six sources: images "Public Domain Mark 1.0"; Colibri dataset CC BY 4.0, credit "Sebastian Schmideler, Sigrun Putjenter, Jörg Lehmann; Staatsbibliothek zu Berlin…"; institution SBB-PK | RUNTIME (read from fixture JSON) |
| Hetzner shared cloud plans listed from EUR 5.49/month excl. VAT ("Regular Performance"); "Cost-Optimized" from EUR 5.99, currently not available | hetzner.com/cloud, fetched 2026-11-15; re-check at order time |

## Step 1: Export consistency (local app)

Honest scope: four separate files cannot be replaced atomically on a plain filesystem. This step does not
claim atomicity. It guarantees that an inconsistent or failed export is never shown as current and stays
visible. True atomicity (versioned export folders with an atomic pointer swap) changes the file layout
users and docs rely on; it is listed under "Not in scope" and needs a separate decision.

Changes:
1. Hold `store.LOCK` for the whole of `run_export` (build and four writes), so two sessions cannot interleave.
2. Add one function that validates an export set against its JSON: all four files exist, parse
   (JSON, CSV, XML), and each companion equals exactly what the current serializers produce from the
   exported JSON's `record` and `exported_at` (`csv_text(csv_rows(...))`, `annotation_page`, `page_xml`).
   This checks content, not just timestamps.
3. `export_state` gains state `incomplete`: JSON readable, change-log ancestry current, companion set
   invalid. Only `current` with a valid set shows "Export aktuell". `incomplete` shows an error naming the
   failing files and the next step (re-export); the round-trip check stays locked, as for `stale`.
4. The CSV preview ("Inhalt der CSV-Datei") is shown only when the CSV belongs to the displayed JSON;
   otherwise it states why it is hidden.
5. A failed export attempt is stored per object in session state (time, file, reason) and shown on every
   rerun until a later export succeeds. Independently, the disk-derived `incomplete` state survives
   restarts and new sessions.
6. `report.FRESHNESS` and `app.py:128` treat `incomplete` as not current.

Consequence to accept: after a future change to a serializer, older exports show as `incomplete` until
re-exported. That is the honest reading, because the companions no longer match what the JSON produces.

Acceptance criteria:
- "Export aktuell" appears only if all four files exist, parse, and match the JSON exactly.
- A write failure at each of the four positions, with and without an earlier export, never yields
  "Export aktuell"; the failure stays visible after `app.run()` reruns.
- Concurrent `run_export` calls for one object produce a valid set (serialized by the lock).
- Existing export tests and the round-trip behaviour stay unchanged for valid sets.

Required tests (`tests/test_app.py`, `tests/test_export.py`):
- Parametrised failure at CSV / annotations / PAGE-XML / JSON write, each with and without a prior export
  (distinct `now_utc`): no "Export aktuell", error visible, still visible after rerun.
- Orphaned CSV without JSON: no CSV preview, state `none`.
- Manually altered annotations or PAGE-XML byte: state `incomplete`.
- Determinism: serializing the same record twice yields identical bytes for all three companions.
- Two threads calling `run_export`: final set valid.

## Step 2: Demo mode in the backend (`BILDLABOR_DEMO=1`)

One module-level flag read once from the environment (in `store`). Off by default: the local app is unchanged.

Complete write, network and subprocess audit, and what demo mode does with each:

| # | Path | Trigger | Demo mode |
|---|---|---|---|
| W1 | `store.write_text` / `write_json` (`store.py:121,148`), incl. temp file in target dir | all writes below | Raise `ReadOnlyDemo` before any filesystem access |
| W2 | `store.save_working_copy` + `snapshot_working_copy` (`store.py:236-262`) | every review action via `update_working_copy` | Raise (guard at entry, before the `.history` snapshot) |
| W3 | Migration save in `store.load_working_copy` (`store.py:231-232`) | merely viewing an old-format working copy | Raise; demo snapshot must need no migration (test) |
| W4 | `actions.run_export` four files | export button | Raise |
| W5 | `actions.run_collection_export` (`actions.py:459`) | collection CSV button | Raise |
| W6 | `imports.commit_import` staging, `write_bytes`, `rename` (`imports.py:104-158`) | import | Raise |
| W7 | `imports.preview_pdf` temp dir + `pdfinfo`/`pdftoppm` (`imports.py:176-210`) | PDF upload | Raise |
| W8 | `imports.preview_iiif` / `download_iiif` -> `fetch_public` | IIIF URL | Raise |
| W9 | `ocr.recognize` temp dir + `tesseract`; `ocr.listing` on render | OCR expander | Raise; never called on render |
| W10 | `proposals.available` (localhost:11434) on render, `propose` | region view | Return unavailable without probing; `propose` raises |
| W11 | `authority.search` cache write + lobid.org request (`authority.py:28,38`) | GND search button | Raise |
| W12 | `similar.build` index write (`similar.py:61`) | "Ähnliche suchen" button | Read prebuilt index from `demo/`; raise if a key is missing |
| W13 | `backup.write_backup` to memory (`backup_view.py:12`) | backup download | Raise (data export of all work data) |
| W14 | `backup.create_backup` / `restore_backup` (`backup.py:74-80,142-155`) | CLI only | Raise |
| W15 | `backup.verify_backup` on uploaded ZIP | file upload | Raise |
| R1 | `st.cache_resource` / `st.cache_data` (ui.py:78, collection_view.py:58,182,261, region_canvas.py:20, library_view.py:10) | rendering | Memory only, keyed by fixed paths; keep. Colibri full-file evaluation (`collection_view.py:222`) raise |
| R2 | Streamlit runtime, Python bytecode, `uv` | process start | Container: run venv Python directly (no `uv run`), `PYTHONDONTWRITEBYTECODE=1`, prebuilt bytecode, `HOME` and `TMPDIR` on a small tmpfs |

Read-only actions kept: navigation, all tabs, region display, METS/MODS comparison, findings (computed in
memory), search, agreement and matrix panels, timeline, HTML report (built in memory), downloads of the
prepared files, and "Export erneut laden und prüfen" (reads JSON, writes only session state).

In demo mode `DATA_DIR` points at the committed `demo/` folder; sources stay in the checkout as today.

Acceptance criteria:
- Every entry W1-W15 refuses in demo mode before touching the filesystem, network or a subprocess.
- With `BILDLABOR_DEMO` unset, the full test suite passes unchanged.
- Rendering every view and tab of all six objects starts no subprocess and opens no socket.

Required tests (new `tests/test_demo.py`):
- Parametrised over every write function in `actions.py`, `imports`, `backup`, `authority`, `similar`,
  `ocr`, `proposals`: raises `ReadOnlyDemo`; the data folder's file list and bytes are unchanged.
- Migration: an old-format working copy in demo mode raises instead of writing.
- Render walk (AppTest) with `subprocess.run`, `socket.create_connection` and `urllib.request.urlopen`
  monkeypatched to fail the test if called.

## Step 3: Demo mode in the interface

- Banner on every page: "Öffentliche Ansicht – nur lesen. Gezeigt werden vorbereitete Prüfungen; Bearbeiten
  ist nur in der lokalen Fassung möglich."
- Hidden: import view and sidebar entry, hero import button, backup section, OCR, Ollama, GND search,
  Colibri full-file evaluation, collection CSV export, absolute export path (`export_view.py:168`).
- Disabled (shown greyed out, so the workflow stays visible): review inputs and buttons, reviewer name,
  decision, approval, second review, "JSON und CSV exportieren".
- Wording next to every demo review: "Demonstrationsprüfung durch den Bewerber, keine unabhängige
  Verifikation, keine Ground Truth."

Acceptance criteria: AppTest walk over all views and tabs of the six objects, no exceptions; every button
and input not on an explicit allowlist is absent or disabled; no absolute filesystem path in any element.

Required tests: the walk above, the allowlist assertion, the banner present on every view, and the
local-mode walk unchanged (snapshot of widget keys).

## Step 4: Curated published data (`demo/`)

Process (performed by the owner, not by automation or by the coding agent):
1. Start the local app on a fresh folder: `BILDLABOR_DATA_DIR=/tmp/demo-build`.
2. Enter only "Shota Tsertsvadze" as reviewer and personally perform each confirmation, decision and approval
   to be published. Objects without a personal review are published in source state, without a name.
3. Export each reviewed object. (No similarity index: the search is hidden in demo mode since step 3.)
4. A build script copies `data/work/*.json` (without `.history`) and the four export files per object into
   `demo/`, writes `demo/MANIFEST.json` with SHA-256 per file, and refuses if any name outside the
   allowlist occurs anywhere.
5. The owner signs `demo/PROVENANCE.md`: which object, which decisions, made personally on which date, and
   the statement that these are demonstration reviews, not independent verification or Ground Truth.

Attribution and licences, shown in the app per object and in `demo/LICENSES.md`:
- Images: Public Domain Mark 1.0, source SBB-PK, with PPN and the original viewer link.
- Colibri classes: Colibri dataset, CC BY 4.0, credit as given in each record, link to the licence,
  note of changes (selection, review decisions).
- METS/MODS metadata: descriptive metadata in SBB's CC BY 4.0 dataset (doi:10.5281/zenodo.13355215);
  no known licence statement for the rest of the complete OAI-PMH files (see `rechtliches/lizenzen.md`).
- Fonts: SIL OFL (existing `static/fonts/OFL-*.txt`).
- Own review contributions: CC BY 4.0, Shota Tsertsvadze (decided 2026-11-21); AI-drafted description and
  keywords stay labelled as such. Code: licence to be chosen by the owner (open item).

`docs/ergebnis/`: it is a real review record (AGENTS.md: preserve) and already public in git history,
including the test names. Decided: leave the tracked file and history untouched; exclude it from the deployment image; stop using it in demo mode
(the start-page example reads from `demo/` instead); add a short note in `docs/ergebnis/README.md` that it
contains early test entries. History rewriting is not proposed (destructive, and the repo is public).

AGENTS.md exception to add: "`demo/` is a deliberately published, curated snapshot with checksums; it is
the only committed working data. Never write to it from the app."

Acceptance criteria:
- `demo/MANIFEST.json` checksums match; no file outside the manifest.
- Only allowlisted names occur in `demo/`; every name occurrence corresponds to an entry in `PROVENANCE.md`.
- Loading `demo/` triggers no migration; every export is `current` and passes the step 1 set validation
  and the round-trip check.
- Every object view shows attribution and licence.

Required tests: manifest integrity; name allowlist scan of all files; no-migration load; export validity
per object; index coverage; attribution present per object (AppTest).

## Step 5: Visual design and UX review (after the curated data, before deployment)

Goal: a professional Digital Humanities / digital collections application, not a generic Streamlit
dashboard. Starts only after `demo/` exists, so the review sees the real published content, and only
after separate approval of the audit findings before any design change.

1. Audit (no changes): first impression of start page and lead example as a library professional;
   hierarchy and reading order; how source images, metadata comparison, decisions and provenance are
   presented; wording and terminology (German, DH/library conventions); consistency with
   `docs/design/DESIGN_SYSTEM.md`; Streamlit artefacts that look like a dashboard; desktop, 375 px and
   keyboard use; contrast and alt texts. Output: ranked findings with screenshots.
2. Approval: the owner selects which findings to fix.
3. Changes: only the selected ones, without new features; local mode unaffected unless approved.

Acceptance criteria: written audit with screenshots of all views (desktop and 375 px); every selected
finding fixed and re-screenshotted; keyboard walk-through documented; full test suite, Ruff, format and
mypy pass; demo tests from steps 2-3 unchanged in intent.

Required tests: existing demo UI tests stay green; new tests only where a change alters behaviour
(for example new or moved controls).

## Step 6: Container (built, run locally only)

- Image from `git archive HEAD` only, so untracked local data (`data/work`, `exports/`, `.claude/`, `dist/`,
  audit files) can never be included; `python:3.13-slim` base, `uv sync --locked --no-dev` at build time,
  venv Python as entrypoint, non-root user.
- Explicit exclusion list on top of `git archive`: `docs/ergebnis/` and any other historical review or
  working records are not copied into the image unless separately approved; the only review data in
  the image is the curated `demo/` folder. A build test lists the image's files and fails on any
  excluded path.
- No Tesseract, Poppler or Ollama in the image.
- Runtime: `--read-only`, tmpfs only for `/tmp` and `$HOME` (16 MiB each, `noexec,nosuid`),
  `--cap-drop=ALL`, `--security-opt no-new-privileges`, `--pids-limit 128`, `--memory 768m`, `--cpus 1`,
  no volumes, `BILDLABOR_DEMO=1`.
- Streamlit flags: `server.address=0.0.0.0` (inside container, published only to host loopback),
  `server.headless=true`, `server.fileWatcherType=none`, `server.runOnSave=false`, `server.maxUploadSize=1`,
  `client.showErrorDetails=none`, `client.toolbarMode=viewer`, `browser.gatherUsageStats=false`;
  XSRF and CORS protection stay default. Options verified to exist in Streamlit 1.67.0.
- Health check `/_stcore/health`.

Acceptance criteria: the container starts with the read-only root filesystem; the AppTest walk passes
against the container image; a write attempt from inside the app fails; no file outside tmpfs changes
(`docker diff` empty); memory measured on Linux under 5 parallel sessions and recorded.

Required tests: CI job that builds the image and runs `tests/test_demo.py` inside it with `--read-only`;
`docker diff` check.

## Step 7: Hosting on Hetzner (documented now, nothing purchased or provisioned)

Resource requirements (measured basis, to be confirmed in step 6): one session about 180 MB; budget
768 MB for the container with headroom for a handful of parallel visitors; disk under 2 GB for OS image
layers. The smallest shared plan (2 vCPU, 4 GB class) is ample.

Recurring costs (verify at order time):
- Server: from EUR 5.49/month excl. VAT (about EUR 6.53 incl. 19 % VAT) per hetzner.com, 2026-11-15.
- Primary IPv4, optional Hetzner backups/snapshots: may cost extra; check the order page.
- Domain: depends on registrar and TLD (open item).
- TLS: free (Let's Encrypt via Caddy).

Security responsibilities of the operator (you):
- OS: Debian or Ubuntu LTS, automatic security updates, reboot policy.
- Access: SSH keys only, no root login, no password login; Hetzner firewall allows 22 (preferably only
  from your IP), 80, 443.
- Caddy: TLS, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `frame-ancestors 'none'`; WebSocket proxy
  to the container on 127.0.0.1. No CSP beyond that until tested against Streamlit.
- Logs: Caddy access logs contain IP addresses; set a short retention (for example 7 days) and state it in
  the privacy notice.
- Monitoring: external uptime check; container restart policy `unless-stopped`.
- Streamlit: set `client.showErrorDetails = "none"` for the public container (default `full` shows stack traces); checked 2026-11-17.
- Updates: rebuild the image for dependency updates (Dependabot already configured); redeploy by tag.

Rollback procedure:
- Every deployment is an image tagged with the git commit; the server keeps the previous two images.
- Rollback = `docker run` of the previous tag with identical flags (one script), then a health check.
- `demo/` is inside the image, so data and code roll back together; there is no server-side state.
- Total loss: a new VPS plus the same script and image rebuild from git; no backups needed for the demo
  itself.

Legal items (engineering guidance, not legal advice; LAWYER where marked):
- Impressum obligation for a privately operated site used for an application: LAWYER.
- Privacy notice for server logs (IP addresses), hosting with Hetzner and its data processing agreement:
  template with placeholders, content to be confirmed: LAWYER.
- METS/MODS metadata licence: see `rechtliches/lizenzen.md` (dataset CC BY 4.0; rest of the OAI files unstated).

Acceptance criteria (runtime on the target, later step): valid TLS; the browser loads no external
resources (network log); no write possible from the UI, and `docker diff` empty after a session walk; all six
objects render; keyboard navigation and a 375 px narrow view checked by hand; privacy notice, Impressum
and licences reachable; uptime monitor green for 7 days before the application link is sent; rollback
rehearsed once.

## Step 8: Fallback

Link the existing screenshots and a short screen recording in the application, so an outage does not
leave reviewers with nothing.

## Not in scope

Truly atomic four-file export (versioned folders); authentication or multi-user editing; live OCR,
models, GND or imports for public visitors; static HTML site; rewriting git history.

## Order of work and approvals

1 -> 2 -> 3 -> 4 (needs your personal review session) -> 5 (visual audit, then approval) -> 6 ->
7 (needs your purchase decision) -> 8.
Each step: tests, `ruff check .`, `ruff format --check .`, `mypy` (CI form), `pytest`, then a short report
before the next step.
