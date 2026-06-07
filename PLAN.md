# Composite Compliance Tracker — Implementation Plan

Companion to `SPEC.md`. Build sequence, acceptance criteria, definition of done. Self-contained.

- **Repo:** `composite-compliance-tracker` (public, under `cognitivefactory-hector`)
- **Approach:** build the **deterministic engines first** (out-time accrual, pot/shelf life, cure-window check, readiness-from-evidence) — they are the trust core and the substance. The checklist UI and the optional LLM assist go on top. Scope: **PAR prepreg hand-layup** only.

> **Illustrative · synthetic data · does not republish AC7118 text (© PRI).** Keep that disclaimer in the README + app footer.

---

## The spine (carry through every milestone)
Keep `DECISIONS.md` open: **Situation · Decision** (incl. rejected tick-box checklist / all-scopes MVP / LLM-decides) **· Risk** (incl. accepted scoped-but-deep) **· Change**. Hardest stance (readiness computed from evidence, not ticks) is the whiteboard centerpiece — `SPEC.md` §3.

## Prerequisites
- Python 3.12, Docker, `gh` authenticated. Optional `ANTHROPIC_API_KEY` (in `.env`, gitignored) only if you build the assist.

---

## Milestones

### M0 — Repo scaffold *(½ day)*
- [ ] Folder + `SPEC.md` + `PLAN.md`; `README.md` (stub + copyright/synthetic disclaimer), `DECISIONS.md` (template from `SPEC.md` §10), `WHITEBOARD-DRILL.md`, `.gitignore` (Python + `.env` + `private_criteria/`), `LICENSE` (MIT).
- [ ] Django + Postgres via `docker-compose.yml`; single `pyproject.toml`; `Dockerfile`; GitHub Actions (ruff + pytest); `/healthz`.
- [ ] `gh repo create … --public --push`.
- **Acceptance:** `docker compose up` serves a page + Postgres; CI green; repo on GitHub.

### M1 — Out-time / shelf-life / pot-life engine (TDD) *(2 days)* — **flagship + safety core**
- [ ] `materials/`: `MaterialLot`, `ColdStorageEvent` (in/out timestamps), `OutTimeEngine` computing **accumulated out-time across freeze/thaw cycles** (accrues only while out), shelf-life (calendar), pot-life (from mix), per-material spec limits with engineering override.
- [ ] Alert thresholds (e.g., 80/90/100%).
- [ ] **Tests first (crown jewels):** multi-cycle accrual sums correctly; time in cold storage does **not** accrue; breach detected at the limit; engineering override changes the limit; expired shelf life flagged.
- **Acceptance:** `pytest` green; multi-cycle out-time + override behave exactly.

### M2 — Cure-cycle records + window check (TDD) *(1–2 days)*
- [ ] `cure/`: `CureSpec` (ramp/soak/pressure/vacuum window), `CureRun` (§8.7.2 fields: facility, equipment, date/time, part serials) + measured profile; deterministic pass/fail vs. window; thermocouple/process-panel presence flags.
- [ ] **Tests:** in-window run passes; an out-of-window soak/ramp fails; missing required field flagged.
- **Acceptance:** `pytest` green; pass/fail matches hand-checked profiles.

### M3 — Criteria model + readiness-from-evidence (TDD) *(1–2 days)* — **the thesis**
- [ ] `compliance/`: `Criterion` (id, paraphrased title, section, scope, evidence-type), `CriterionStatus`, `NCR`, `EvidenceLink`. `readiness/` computes a criterion's status **from linked evidence** (e.g., §5.1.12 green only if all active lots have current in-limit out-time records); documentation-only criteria require an attached procedure ref to go green.
- [ ] **Tests:** a criterion with a missing/expired evidence record computes **NOT ready** (never auto-green); an NA requires an explanation; a NO opens an NCR.
- **Acceptance:** `pytest` green; "missing record → not ready" is a passing test.

### M4 — Synthetic corpus + representative criteria *(1 day)*
- [ ] Author the fictional shop: prepreg/adhesive lots (with invented out-time/shelf specs), cure specs, parts, freeze/thaw histories incl. **one lot near an out-time breach** and **one expired lot**; ~20–30 **paraphrased** AC7118 criteria across §4/§5/§6/§8 (NO verbatim text). Fixed seed.
- **Acceptance:** seed loads; readiness dashboard shows a realistic mix of ready/gap/NCR.

### M5 — UI: Readiness / Out-time / Cure / Traceability *(2–3 days)*
- [ ] Readiness dashboard (% by section, gaps, NCRs); out-time gauges + freeze/thaw timeline + alerts; cure profile charts (Plotly) vs. window; lot→kit→part genealogy; **click a "ready" status → its evidence record + the criterion.**
- [ ] Footer disclaimer (illustrative · synthetic · not republishing AC7118).
- **Acceptance:** seed → dashboard; an out-time alert is visibly firing; a cure pass/fail renders; clicking a green criterion reveals real evidence.

### M6 — (Optional) Claude assist *(1 day, can defer)*
- [ ] `assist/`: import a user-supplied AC7118 export → structured `Criterion` rows; draft NCR explanation / readiness narrative. Human-edited; **never decides compliance or computes a limit**; gated on `ANTHROPIC_API_KEY`.
- [ ] Tests (mocked API): assist output is advisory; status/limits are unaffected by it.
- **Acceptance:** with no key, app is fully usable; with a key, assist drafts text only. *(If building in Claude Code, invoke the `claude-api` skill.)*

### M7 — Polish, README, deploy *(1 day)*
- [ ] `README.md`: what/why, one-command run, screenshots/GIF, disclaimers, links.
- [ ] Deploy to Render via `render.yaml`; migrate on start; `/healthz`; optional `composite.hector-garza.com`.
- **Acceptance:** public URL works from a fresh browser; full flow runs deployed.

### M8 — Decision Record + Whiteboard drill *(½ day)* — **the differentiator**
- [ ] Complete `DECISIONS.md`; run the `WHITEBOARD-DRILL.md` (text); record later when a mic is available.
- [ ] Capture the "not ready because the record is missing" example explicitly.
- **Acceptance:** a stranger can read `DECISIONS.md` and explain why readiness is computed from data, not ticked.

---

## Testing strategy
- **Crown jewels (test hardest, first):** out-time multi-cycle accrual + override; cure-window pass/fail; **readiness-from-evidence incl. "missing record → not ready."**
- Mock Anthropic in any assist tests; keep heavy/LLM out of CI. CI = ruff + the deterministic tests.

## Suggested repo layout
```
composite-compliance-tracker/
├── README.md SPEC.md PLAN.md DECISIONS.md WHITEBOARD-DRILL.md
├── Dockerfile docker-compose.yml .env.example pyproject.toml render.yaml
├── config/ (settings urls asgi/wsgi)
├── tracker/
│   ├── compliance/  models.py readiness.py
│   ├── materials/   models.py outtime.py        # deterministic engine
│   ├── cure/        models.py window.py
│   ├── trace/       models.py
│   ├── assist/      client.py prompts.py          # optional, gated
│   ├── data/        seed.py  criteria_repr.py     # synthetic + paraphrased
│   └── views.py / templates/
└── tests/ test_outtime.py test_cure.py test_readiness.py test_seed.py
```

## Risk register (project execution)
| Risk | Mitigation |
|---|---|
| Republishing copyrighted AC7118 text | Paraphrased/representative criteria only; real text imported privately (gitignored `private_criteria/`); say so in README. |
| "It's just a checklist" perception | Lead with evidence-mapping + the out-time engine; the green status is data-backed. |
| Out-time math wrong (the whole point) | TDD the multi-cycle accrual + override hardest; it's the crown jewel. |
| Scope creep into all 7 scopes | PAR hand-layup only in MVP (Non-Goals); note the generalization. |
| LLM appears to judge compliance | Deterministic core decides; assist is advisory + gated + tested. |
| Leaking secrets / employer data | `.env` gitignored; Render secret; synthetic data only. |
| Skipping M8 | M8 *is* the portfolio — the data-backed-readiness story. |

## Definition of Done
See `SPEC.md` §8 — app + decision record (+ later whiteboard) linked; the deterministic engines tested; and "missing record → not ready" demonstrated and tested.
