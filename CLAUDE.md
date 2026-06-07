# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status: pre-code scaffold

Only the design docs exist (`SPEC.md`, `PLAN.md`, `DECISIONS.md`, `WHITEBOARD-DRILL.md`, `README.md`). No Django project, `pyproject.toml`, `Dockerfile`, or tests have been created yet. Build follows `PLAN.md` milestones **M0 → M8** in order. When implementing, treat `SPEC.md` (the what/why) and `PLAN.md` (the build sequence + acceptance criteria) as the source of truth, and update `DECISIONS.md` as engineering choices are made.

## What this project is

A NADCAP **AC7118 (Composites)** audit-readiness tracker, scoped to the **PAR prepreg hand-layup** path. The thesis — and the thing every change must protect — is that **a criterion's "ready" status is *computed* from linked, valid process records, never manually ticked**. Clicking a green status lands on the evidence record that proves it. It is a portfolio piece (one of three equal deliverables: app + `DECISIONS.md` + a deferred whiteboard recording); the design judgment matters as much as the working code.

## Non-negotiable constraints

These are the project's reason for existing. Violating one defeats the point.

1. **Deterministic core, never an LLM.** Out-time accrual, pot-life, shelf-life, cure-window pass/fail, and readiness-from-evidence are plain, tested Python. An LLM must **never** compute a time limit or decide compliance. The optional Claude assist (gated on `ANTHROPIC_API_KEY`) is **advisory only** — it drafts NCR/readiness text and imports user-supplied criteria text; its output never changes a status or a limit. Tests must prove the assist can't affect outcomes.
2. **No verbatim AC7118 text in the repo.** AC7118 is © Performance Review Institute. Ship only **paraphrased/representative** criteria referenced by ID + short title (e.g., `5.1.12 — accumulated out-time/pot-life tracked to spec limits`). Real text is imported privately into the **gitignored `private_criteria/`**. Never paste the standard's text into code, seeds, tests, or commits.
3. **Synthetic data only.** Fictional shop, lots, cure specs, parts, operators — obviously synthetic, fixed seed. **No employer/TAT/MSI data or IP, ever.**
4. **No auto-disposition.** The tool is a readiness *aid*; a qualified human signs. No auto-NCR-closure, no auto-disposition.
5. **Engineering takes precedence.** A customer/engineering spec value overrides a built-in default limit, and the app records which value governed. Build this into the limit-resolution logic, not as an afterthought.
6. **Never commit secrets.** `ANTHROPIC_API_KEY` lives in `.env` (gitignored) locally and as a Render secret in prod.

## Architecture (planned)

Django + Postgres backend, Django templates + HTMX frontend, Plotly charts. Python 3.12, single `pyproject.toml`, ruff + pytest, GitHub Actions CI, Docker, deployed to Render (`render.yaml`) behind Cloudflare.

Per-app responsibilities (under `tracker/`):
- **`materials/`** — `MaterialLot`, `ColdStorageEvent` (in/out timestamps), and `outtime.py`: the deterministic out-time engine. Out-time **accrues only while a lot is out of cold storage**, summed across multiple freeze/thaw cycles, vs. per-material spec limit (engineering-overridable). Also pot-life (from mix), shelf-life (calendar), and alert thresholds (e.g. 80/90/100%) that fire **before** breach.
- **`cure/`** — `CureSpec` (ramp/soak/pressure/vacuum window), `CureRun` (§8.7.2 fields: facility, equipment, date/time, part serials), and `window.py`: deterministic pass/fail of measured profile vs. spec window.
- **`compliance/`** — `Criterion`, `CriterionStatus`, `NCR`, `EvidenceLink`. A NO opens an NCR; an NA requires an explanation.
- **`readiness/`** — computes a criterion's status **from its linked evidence** (e.g. §5.1.12 is green only if every active lot has a current, in-limit out-time record). Documentation-only criteria need an attached procedure reference to go green. This module embodies constraint #1 of the thesis.
- **`trace/`** — Lot → Kit → Part genealogy, CoC, receiving.
- **`assist/`** — optional, gated Claude integration (`client.py`, `prompts.py`). Advisory only.
- **`data/`** — `seed.py` (synthetic shop corpus, fixed seed) + `criteria_repr.py` (paraphrased criteria across §4/§5/§6/§8). The seed must include **one lot near an out-time breach** and **one expired lot** so the "NOT ready because the record is missing/expired" demo is real on screen.

## Build order & testing

Build the **deterministic engines first, test-first** (M1 out-time → M2 cure → M3 readiness), *then* the seed (M4), UI (M5), optional assist (M6), deploy (M7), decision record (M8). The engines are the trust core; the UI sits on top.

**Crown-jewel tests (write these hardest, first):**
- Multi-cycle out-time accrual sums correctly; time in cold storage does **not** accrue; breach detected at limit; engineering override changes the limit; expired shelf life flagged.
- Cure-window: in-window passes, out-of-window soak/ramp fails, missing required field flagged.
- Readiness-from-evidence: **a missing/expired evidence record computes NOT ready (never auto-green)** — this is the single most important test in the project.

Mock Anthropic in any assist tests; keep LLM calls out of CI. CI = ruff + the deterministic tests.

## Commands (once M0 scaffolds them — per PLAN.md)

These don't exist yet; create them in M0 to match this contract:
- `docker compose up` — serves the app + Postgres (with `/healthz`).
- `pytest` — run the test suite; `pytest tests/test_outtime.py::<name>` for a single test.
- `ruff check .` — lint.
