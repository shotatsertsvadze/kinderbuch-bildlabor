- Preserve source fixtures and real review records; use temporary data for tests.
- Do not commit working data, exports, credentials, or local backups.

<!-- gg:init:start -->
# Kinderbuch-Bildlabor

Local German-language Streamlit workbench for reviewing historical children's-book illustrations against saved images and OAI/METS/MODS metadata; no live fetching or OCR execution.

## Review and persistence traps
- Opening the collection loads every object; loading legacy working copies can persist migrations. Set `BILDLABOR_DATA_DIR` BEFORE importing app/store for UI checks or demos. It relocates only working copies and exports, never catalog/source fixtures; AppTest isolation patches `DATA_DIR`, `WORK_DIR`, and `EXPORT_DIR` together.
- Load/change/save is one transaction under a reentrant thread lock: multiple browser sessions in one process are supported, multiple servers sharing a data directory are not.
- Before overwriting a working copy (including migrations), preserve its exact previous bytes in content-addressed `.history` snapshots. A mismatched existing snapshot must block replacement, not be treated as a usable backup.
- Region geometry, keywords, description, and each transcription field have independent confirmations. Content edits invalidate the affected confirmation and active final approval; no-op saves must preserve both and write nothing. Historical confirmations remain in `review_log`.
- UI synchronization compares input/baseline/saved: untouched input follows newer saved content; edited conflicts retain input but cannot overwrite it. Keep store-side seen-value checks too; final approval compares the entire displayed record with the latest saved record.
- Final approval is not Ground Truth: require name, acknowledgment, completed areas, and fresh validation under the store lock. Only `RECORD_FINAL_REVIEW` is excluded from technical/review blockers; optional NOT_RUN checks stay visible but nonblocking.
- Reasoned decisions convert eligible findings to DOCUMENTED, not erase evidence. Identity includes exact code/message; classification depends on illustration geometry, imprint context on publisher transcription. Basis edits invalidate decisions while retaining history. “Nicht entscheidbar” still blocks. Explicit unchanged reconfirmation records person/time, revokes approval and stales exports; ordinary no-op decision saves do not.
- Export freshness follows change-log ancestry, not timestamps or text equality: empty suffix=current, nonempty=stale, mismatched prefix=foreign history. Round-trip results describe current exports only. CSV formula neutralization is serialization-only; never alter JSON or records to match it.
- Book MODS is selected through the logical METS root's DMDID, not a fixed section. Keep publication versus digitization publishers and book metadata versus printed imprint separate; literal typographic differences are intentional comparison evidence, not normalization targets.

## Isolated local launch
`BILDLABOR_DATA_DIR=/tmp/bildlabor-fresh uv run streamlit run app.py` from the checkout; choose a new directory for a clean source state. The checked-in launcher does not isolate data. Streamlit binds localhost; a package build alone does not supply checkout-relative catalog/source assets.
<!-- gg:init:end -->

<!-- gg-safe:blocked-packages:start -->
## Blocked packages
GG Coder's safety checks blocked these. Never install or run them; use another version or package.
- PyPI `python`: lookalike of "cython"
<!-- gg-safe:blocked-packages:end -->
