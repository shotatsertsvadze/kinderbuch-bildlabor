- Preserve source fixtures and real review records; use temporary data for tests.
- Do not commit working data, exports, credentials, or local backups.

<!-- gg:init:start -->
# Kinderbuch-Bildlabor

Local German-language Streamlit workbench for reviewing historical children's-book illustrations against saved images and OAI/METS/MODS metadata; it does not fetch live sources or run OCR.

## Data and review invariants
- `sammlung/katalog.json` selects the source bundle for each object. Source fixtures stay immutable; edits belong to working copies with source checksums and change history.
- Loading an existing working copy can WRITE: legacy description/transcription status migrations are persisted and logged. Even opening the collection loads every object. Use an isolated data directory for demonstrations and UI verification, not real working records.
- `BILDLABOR_DATA_DIR` is read at import and relocates only working copies (`data/work/`) and exports (`exports/`), not catalog or source fixtures.
- Persistence uses atomic replacement and a reentrant thread lock around load/change/save. This supports multiple browser sessions in ONE server process, not multiple servers sharing a data directory.
- Preserve independent confirmations for region geometry, keywords, description, and each transcription field. Actual content edits invalidate the affected area and active final approval; no-op edits must not invalidate anything. Historical confirmations remain in `review_log`.
- Final object approval is not Ground Truth. It requires a named reviewer, acknowledgment, all areas confirmed, and current validation under the store lock. Only the circular `RECORD_FINAL_REVIEW` finding is excluded from substantive blockers; optional NOT_RUN checks are visible but nonblocking. Do not dismiss existing review items or MODS differences to enable approval.
- Session edits use three-way comparison (input/baseline/saved): untouched fields follow newer saved content, edited conflicts retain input but cannot overwrite it. Final approval compares the entire displayed record with the latest saved record.
- Export freshness is change-log ancestry, not timestamp comparison: an empty suffix is current, a nonempty suffix is stale, and no common prefix is foreign history. Round-trip checks only describe current exports.
- Book-level MODS comes from the logical METS root's DMDID, not a fixed section ID. Publication and digitization publishers, and book metadata versus printed illustration text, are different contexts. Metadata comparison deliberately preserves literal typographic differences rather than normalizing them away.

## Local workflow
- Isolated demo: `BILDLABOR_DATA_DIR=/tmp/bildlabor-demo uv run streamlit run app.py`. Choose a fresh directory when the demo must start clean. Streamlit is configured for localhost only.
<!-- gg:init:end -->
