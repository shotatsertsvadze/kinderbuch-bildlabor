# Coding agents

See CLAUDE.md, when available, for additional agent-behavior instructions.

- Install: `uv sync --locked`
- Build: `uv build`
- Test: `uv run --locked pytest`
- Run: `uv run streamlit run app.py`
- Lint: no linter is configured.
- CI lives in `.github/workflows/ci.yml` and must stay green.
- Never commit with `--no-verify`.
- Preserve source fixtures and real review records; use temporary data for tests.
- Do not commit working data, exports, credentials, or local backups.
