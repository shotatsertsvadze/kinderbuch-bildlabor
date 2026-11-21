# Compliance register

Snapshot: 2026-11-17, commit 5eff73c. Engineering guidance, not legal advice. Nothing here declares the project compliant.

## Exposure profile (assumed unless marked confirmed)

- Today: a local application with no accounts, no tracking and no deployment. Optional network calls (GND search, IIIF import, local Ollama) happen only on a button press and are refused in demo mode. Confirmed from code.
- Planned: a public read-only demo on a Hetzner VPS (EU) for a job application, with the owner's name in published review records.
- Reach: worldwide, main regime Germany/EU. No payments, no user uploads, no minors expected. Assumed.

## Open items

| ID | Severity | Item | Evidence | Needs |
|---|---|---|---|---|
| C1 | Blocker before publishing | Impressum and privacy notice exist as templates in `rechtliches/` (shown in demo mode); `OFFEN:` fields and the Hetzner processing agreement are open; the image build fails while `OFFEN:` remains. Caddy keeps no access log | rechtliches/, Dockerfile | Owner fills in; lawyer if unsure |
| C2 | High | No licence for the code. Own review contributions: decided 2026-11-21, CC BY 4.0 (Shota Tsertsvadze), recorded in `demo/LICENSES.md` and `rechtliches/lizenzen.md` | no LICENSE file; GitHub shows none | Owner chooses code licence |
| C3 | Medium | Descriptive METS/MODS metadata of both works: in SBB's CC BY 4.0 dataset (doi:10.5281/zenodo.13355215, verified 2026-11-21). The complete OAI-PMH XML files (METS structure, file references, administrative data) have no known licence statement; stated as such in `demo/LICENSES.md` and `rechtliches/lizenzen.md` | public-demo-plan.md, step 4 | Owner checks SBB terms |
| C4 | Medium | `docs/ergebnis/` is public in git history and names test identities and the owner | decided: no history rewrite, excluded from the image | Accept or lawyer |
| C5 | Lawyer | The owner's full name as reviewer in published data (review content licence decided: CC BY 4.0) | public-demo-plan.md step 4 | Lawyer |

## Implemented controls (verified by code reading or tests)

- Demo mode refuses writes, network calls, import, backup and external programs (`store.refuse_in_demo`, tests/test_demo.py).
- Attribution per object (Public Domain Mark 1.0, Colibri CC BY 4.0 with credit) is shown on all six object pages in demo mode (browser check, 2026-11-17).
- Fonts are local (SIL OFL); Streamlit usage statistics are off (`.streamlit/config.toml`).
- No third-party requests: the page icon was a Material symbol that the browser fetched from
  fonts.gstatic.com on every visit; replaced by `static/favicon.png`. Browser walk over all views on
  2026-11-20 contacted only the demo server.

## Not checked

Hosting contract terms, accessibility law for the public site (WCAG checks only), cookie behaviour of a running public site, third-party requests on the deployed site (to be observed once it exists).
