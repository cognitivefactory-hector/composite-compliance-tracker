# Decision Record — Composite Compliance Tracker

First-draft answers (from `SPEC.md` §1.1) — pressure-test in the whiteboard drill (`WHITEBOARD-DRILL.md`), keep what survives. Recording deferred until a mic is available; this written record carries the judgment for now.

## Situation
A composites shop pursuing/holding NADCAP **AC7118** accreditation must satisfy ~30 sections across up to 7 scopes **and** continuously track time-sensitive process data: prepreg/adhesive **accumulated out-time and pot life vs. spec limits** (§5.1.12), cold-storage temperature logs (§6.1.1), **cure-cycle records** — facility, equipment, date/time, part serials (§8.7.2), lot/CoC traceability (§5.1.5/§5.1.9), operator training (§4.5). Most shops run this on paper and spreadsheets — and AC7118 §4.4 *audits the spreadsheets themselves*. Facts I have: the public criteria + the production data. Facts I'm missing: a live link between a record and the criterion it proves, and a proactive alarm **before** a time limit is blown.

## Decision
A tracker that (a) encodes AC7118 criteria as a structured **readiness checklist** (YES/NO/NA, existence·adequacy·compliance, NCRs for negatives) and (b) tracks the **data-heavy controls** — and **maps each record to the criterion(s) it provides objective evidence for**, so a section's readiness is *computed* from real records. All time-limit math is **deterministic code**, not an LLM.
**Rejected:** a generic tick-box checklist (an unbacked "yes" is what auditors distrust); covering all 7 scopes/30 sections in the MVP (scope to **PAR prepreg hand-layup**, go deep); letting an LLM decide compliance.

## Risk
Killers: a **silent out-time/shelf-life excursion** (prepreg used past its allowable out-time → latent defect, escape/scrap), and an **audit finding from a missing/unlinked record**; plus a green dashboard that isn't evidence-backed. Mitigations: **proactive alerts before** out-time/pot-life/shelf-life limits; deterministic time-math with freeze/thaw accrual rules; every "ready" status traceable to a record **and** criterion; **"engineering takes precedence"** (spec overrides default limits).
**Consciously accepted:** scoped coverage (one path, done right) over shallow full coverage; the tool is a readiness aid — a qualified person still dispositions.

## Change
Audit prep goes from a frantic paper-chase to a live readiness dashboard; out-time excursions are **prevented, not discovered at MRB**; every compliance claim is backed by a linked record. The prevented loss: a scrapped/escaped part from a blown out-time, and a finding from a missing record.

## Whiteboard session
- Recording: _deferred — no mic yet_
- The "NOT ready because the evidence record is missing/expired" example: _…_
- Why deterministic math, not the LLM: _safety-relevant time limits can't depend on a model's arithmetic._

---

## Engineering decisions (recorded as built)
- **Backend:** Django + Postgres — one stack across the portfolio. Plotly for cure profiles / out-time gauges; HTMX UI.
- **Deterministic core first:** out-time accrual (multi-cycle, accrues only while out of cold storage), pot/shelf life, cure-window pass/fail, and readiness-from-evidence are tested Python; the LLM never computes a limit or decides compliance.
- **Copyright guardrail:** AC7118 text is © PRI — the public repo ships only paraphrased/representative criteria (by ID); licensed users import the real text into a gitignored `private_criteria/`.
- **Optional Claude assist:** gated on `ANTHROPIC_API_KEY`; advisory only (criteria import + NCR/readiness drafting).
- **Host:** Render (Dockerized + Postgres) behind Cloudflare. Secrets never committed; synthetic shop data only.
