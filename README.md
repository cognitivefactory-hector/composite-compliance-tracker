# Composite Compliance Tracker

A NADCAP **AC7118 (Composites)** readiness + process-data tracker — it logs the time-sensitive controls a composites shop lives or dies by (prepreg **out-time**, **cure cycles**, lot traceability) and **maps every record to the AC7118 criterion it provides objective evidence for**, so audit readiness is *computed from data*, not self-attested on a checklist.

> **Status:** scaffolded (spec + plan in place). Build follows `PLAN.md` (M0 → M8).
> **⚠ Illustrative tool on synthetic data — not a quality system of record; a qualified person signs.** No employer data, ever. **Does not republish the copyrighted AC7118 text** (© Performance Review Institute) — it references criteria by ID + paraphrased titles and lets a licensed user import the real text privately.

Part of [hector-garza.com](https://hector-garza.com)'s portfolio. One of three equal deliverables: the app, a **Decision Record** ([`DECISIONS.md`](./DECISIONS.md)), and a recorded whiteboard session (deferred — written `DECISIONS.md` carries it for now). A working demo no longer proves competence — the judgment behind it does. See [`SPEC.md`](./SPEC.md) §0.

## What it does (MVP scope: PAR prepreg hand-layup)
- **AC7118 readiness checklist** — criteria by section with Compliant / Gap / NA-explained status, the existence·adequacy·compliance model, NCRs for negatives, and a dashboard (% ready by section, open gaps).
- **Out-time / shelf-life / pot-life tracker (flagship → §5.1.12)** — per lot: freeze/thaw events, **accumulated out-time across cycles** (accrues only while out of cold storage), shelf/pot life, per-material spec limits with engineering override, and **proactive alerts before a limit is blown**.
- **Cure-cycle records (→ §8.7.2)** — facility, equipment, date/time, part serials, the time/temp/pressure/vacuum profile vs. the cure-spec window (deterministic pass/fail) with a Plotly chart.
- **Lot / CoC / traceability (→ §5.1.5/§5.1.9)** — lot → kit → part genealogy.
- **Evidence mapping (the killer feature)** — a criterion goes green only when its linked records exist and are valid. Click a "ready" status → land on the proof.

## Tech stack
- **Backend:** Django + Postgres · **Charts:** Plotly · **Frontend:** Django templates + HTMX
- **Deterministic core** (out-time accrual, pot/shelf life, cure-window, readiness-from-evidence) — plain tested Python, never an LLM
- **Optional Claude assist** (gated on `ANTHROPIC_API_KEY`): import a licensed AC7118 export → structured criteria; draft NCR/readiness text — advisory only, never decides compliance
- **Packaging:** Docker · Python 3.12 · **Quality:** pytest + ruff + GitHub Actions CI

## Deployment
Dockerized Django + Postgres on **Render** (`render.yaml`), fronted by **Cloudflare** (planned `composite.hector-garza.com`). `ANTHROPIC_API_KEY` (if the assist is enabled) is a Render secret — never committed.

## Links (filled in as the build progresses)
- 🔗 Live demo: _TBD_
- 🧠 Decision record: [`DECISIONS.md`](./DECISIONS.md)
- 🎥 Whiteboard walkthrough: _TBD (deferred — no mic yet)_

## Build
See [`PLAN.md`](./PLAN.md) — the deterministic engines (out-time, cure-window, readiness-from-evidence) are built **first**, test-first; the checklist UI and optional LLM assist go on top.
