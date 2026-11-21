# Read-only portfolio and deployment audit

## Goal
Produce the requested nine-part evidence-based audit for the SBB-IIIK-1-2026 application, ending with five prioritized actions. No implementation, installation, deployment, repository indexing, or changes to working records. This approval-plan file is the only repository write.

## Approach
Trace actual code, callers, fixtures and tests rather than treating documentation as proof. Preliminary reading already shows documentation drift: `app.py` describes no network/OCR, while README documents explicit IIIF imports and local OCR; `docs/BEZUG_ZUR_STELLE.md` lists PAGE export as future work while `actions.py:pagexml_path` and `docs/OFFENE_PUNKTE.md` describe it as implemented. Resolve these through code and tests.

Inspect `app.py:load_collection/object_page`; `src/kinderbuch_bildlabor/store.py`, `review.py`, `validate.py`; `actions.py:run_export/approve_object/second_review_object`; `imports.py:commit_import/preview_pdf/preview_iiif`; `import_transport.py:public_address/fetch_public`; `oai.py:book_mods/mapping_rows/compare`; `export.py:later_changes/roundtrip_report`; `annotations.py:annotation_page`; `backup.py:verify_backup/restore_backup`; OCR, proposals, authority, similarity, UI and static assets with their corresponding `tests/test_*.py`. Inspect `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, `.streamlit/config.toml`, catalog and source-rights metadata, and relevant documentation. Do not inspect private working records unnecessarily or display credentials.

Load durable and compliance-guard checklists before recoverability/legal verdicts. Work without delegation. Compare vacancy alignment against repository evidence; seek the public original vacancy if accessible, otherwise explicitly label requirements supplied by the user rather than claiming independent verification.

## Risks and verification
Loading application/store can migrate records. Never launch or import against the real data directory. First inspect test isolation and all side effects. Run only existing installed tools, without uv synchronization/downloads, using disabled bytecode and caches. Tests may write only disposable temporary test data outside the checkout; if safe isolation cannot be established, report execution blocked rather than run them. Do not build packages or start network integrations. Distinguish tests actually run, mocked integrations, historical reports, and static-only findings.

Candidate checks, after confirming installed executables and isolation: `.venv/bin/ruff check --no-cache .`, `.venv/bin/ruff format --check --no-cache .`, `.venv/bin/mypy --cache-dir=/dev/null`, and `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider -q` with application data redirected to disposable temporary storage. If the read-only restriction precludes temporary test files, provide static coverage analysis and explicitly unrun commands instead. Compare read-only git status before and after without showing private file contents.

## Steps
1. Inventory tracked code, tests, assets, configuration and installed tools; establish safe test isolation and source evidence locations.
2. Trace collection loading, review/edit/confirmation, metadata mapping, import/OCR, export and backup flows through callers and tests.
3. Assess public-demo security, privacy, licensing and recoverability with the applicable checklists and path-level evidence.
4. Run permitted installed checks under verified isolation, recording exact results and integration limitations without modifying project data.
5. Deliver all nine requested report sections with evidence, vacancy alignment, German verified-functionality description, and P0/P1/P2 acceptance criteria; finish with the five highest-priority next actions.
