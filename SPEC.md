# Composite Compliance Tracker — Design Spec

**Project 9 of the Hector Garza portfolio.** Self-contained: everything needed to start this as its own repository is in this file and its companion `PLAN.md`.

- **Owner:** Hector Garza · hectorg@smartxchain.com · hector-garza.com
- **Status:** Spec — ready to build
- **Suggested repo name:** `composite-compliance-tracker`
- **One-liner:** A NADCAP **AC7118 (Composites)** readiness + process-data tracker — it logs the time-sensitive controls a composites shop lives or dies by (prepreg out-time, cure cycles, lot traceability) and **maps every record to the AC7118 criterion it provides objective evidence for**, so audit readiness is *computed from data*, not self-attested on a checklist.

> **Illustrative tool on synthetic data.** Not a quality system of record; a qualified person signs. No employer data, ever. **Does not republish the copyrighted AC7118 text** — see §5.

---

## 0. Read this first — what this project is *really* for

A demonstration that you can turn a brutal regulatory standard into a working data system — built by someone who's actually been audited. It is **not** a checklist app where you tick "yes, we comply." The hireable signal is the **link between live process data and the requirement it satisfies**: an auditor (and a hiring manager) can click a green "ready" status and land on the actual out-time log or cure record that proves it.

Three deliverables of equal weight:
1. **The working app** (hosted, clickable).
2. **A Decision Record** (`DECISIONS.md`) on the four questions below.
3. **A recorded whiteboard session** defending the design (deferred until a mic is available — written `DECISIONS.md` carries it for now).

---

## 1. The spine — four questions that make judgment portable

> **1 · Situation** — what's happening, the constraints, the facts you have and the facts that are *missing*.
> **2 · Decision** — the path taken and the credible options *rejected*.
> **3 · Risk** — what could go wrong, what you removed, what you *consciously accepted*.
> **4 · Change** — what's different now; the judgment tied to a real change.

### 1.1 First-draft answers (defend/revise on camera)

- **Situation.** A composites shop pursuing or holding NADCAP **AC7118** accreditation must satisfy ~30 sections across up to 7 scopes (PAR/prepreg, metal bond, core, liquid resin, compression molding, kitting, edge seal) **and** continuously track time-sensitive process data: **prepreg/adhesive accumulated out-time and pot life vs. spec limits** (AC7118 §5.1.12), cold-storage temperature logs (§6.1.1), **cure-cycle records** — facility, equipment, date/time, part serials (§8.7.2), lot/CoC traceability (§5.1.5/§5.1.9), operator training (§4.5). Most shops run this on paper and spreadsheets — and AC7118 §4.4 *audits the spreadsheets themselves*. Facts I have: the public criteria + the production data. Facts I'm missing: a live link between a record and the criterion it proves, and a proactive alarm **before** a time limit is blown.
- **Decision.** Build a tracker that (a) encodes AC7118 criteria as a structured **readiness checklist** (YES/NO/NA, with the existence/adequacy/compliance model and NCRs for negatives), and (b) digitally tracks the **data-heavy controls** — and **maps each record to the criterion(s) it provides objective evidence for**, so a section's readiness is *computed* from real records. All time-limit math (out-time accrual, pot life, shelf life, cure-window pass/fail) is **deterministic code**, not an LLM. **Rejected:** a generic tick-box checklist (an unbacked "yes" is exactly what auditors distrust); **rejected** covering all 7 scopes/30 sections in the MVP — I scope to **PAR prepreg hand-layup** and go deep; **rejected** letting an LLM decide compliance.
- **Risk.** The killers: a **silent out-time / shelf-life excursion** — prepreg used past its allowable out-time → a latent defect that escapes or scraps a part; and an **audit finding from a missing or unlinked record**. Also: a green "ready" dashboard that isn't actually backed by evidence. Mitigations: **proactive alerts before** out-time/pot-life/shelf-life limits; deterministic time-math with the freeze/thaw accrual rules; every "ready" status is traceable to a record **and** the criterion; **"engineering takes precedence"** (a customer/engineering spec overrides a default limit). **Consciously accepted:** scoped coverage (one path, done right) over shallow full coverage; the tool is a *readiness aid* — a qualified person still dispositions.
- **Change.** Audit prep goes from a frantic paper-chase to a live readiness dashboard; out-time excursions are **prevented, not discovered at MRB**; every compliance claim is backed by a linked record. The prevented loss: a scrapped/escaped part from a blown out-time, and a finding from a missing record.

---

## 2. Why this project (market fit + your edge)

- **Regulated-quality + data engineering** in one — pairs with RCCA Copilot and Spec Compliance Checker as the "I automate quality work without breaking the rules that govern it" cluster.
- Composites is a growing aerospace segment; AC7118 accreditation is a hard, expensive, perennial pain. The buyer feels it.
- **Your unfair advantage is rare:** you've been the audited *and* the auditor — you know what "objective evidence" means, why a missing out-time card is a finding, and why a green checkbox isn't proof. Almost no AI engineer can model AC7118 correctly; almost no composites quality lead can build the app. You're both.

---

## 3. The staged whiteboard session (deferred recording)

Use the drill in `WHITEBOARD-DRILL.md`. Capture survivors in `DECISIONS.md`; record later when a mic is available.

### 3.1 Adversarial challenge script
1. **"This is a checklist app — a fancy spreadsheet. Where's the engineering?"** *(The data→criterion evidence mapping; deterministic out-time/cure-window math; readiness computed from records, not checkboxes.)*
2. **"Out-time tracking is just subtraction. Why is it hard or valuable?"** *(Accumulated out-time across multiple freeze/thaw cycles, accrual only while out of cold storage, thaw-before-open and reseal rules, per-material spec limits, alerting before breach — and the scrap/escape cost of getting it wrong.)*
3. **"AC7118 has 7 scopes and 30 sections. You did one path — why be impressed?"** *(Scoping judgment: depth over shallow breadth; the data model generalizes; honest about coverage.)*
4. **"AC7118 §4.3/§4.4 means an auditor distrusts your software and spreadsheets. How does your app pass its own standard?"** *(Validation, audit trail, traceable evidence, human sign-off, change control, "engineering takes precedence.")*
5. **"Synthetic data, not a real accredited shop — why believe it?"** *(Criteria are public; the data model reflects the real controls; first validation is against a real shop's records.)*
6. **"Show me a status the app flagged NOT ready that a human would've ticked 'yes.'"** *(Data-backed readiness catching an unbacked claim — the thesis.)*

---

## 4. Product specification

### 4.1 Users
- **Primary:** a composites quality/process engineer maintaining AC7118 readiness and the daily process records.
- **Demo viewer:** a hiring manager who clicks a "ready" status and sees the actual evidence behind it in 60 seconds.

### 4.2 Core features (MVP — scoped to PAR prepreg hand-layup)
1. **AC7118 readiness checklist.** Criteria (by section/subsection) with status **Compliant / Gap / NA-explained**, the existence·adequacy·compliance dimensions, an **NCR** record for each NO, and required explanation for each NA. A **readiness dashboard**: % ready by section, open NCRs/gaps.
2. **Out-time / shelf-life / pot-life tracker (the flagship module → §5.1).** Per material **lot**: freezer in/out events, **accumulated out-time** computed across cycles (accrues only while out of cold storage), shelf-life expiration, pot-life for mixed resin/adhesive; **proactive alerts** at configurable thresholds before each limit; thaw-before-open and reseal-before-return checks. Per-material spec limits (engineering/customer overrides default).
3. **Cure-cycle records (→ §8.7.2 / §8.1).** Log each cure: facility, equipment ID, date/time start, **part serials/control numbers in the cycle**, the time/temp/pressure/vacuum profile vs. the cure spec window, thermocouple placement, and concurrent process-control panel reference. Pass/fail against the window (deterministic) + a Plotly profile chart.
4. **Lot / CoC / receiving traceability (→ §5.1.5/§5.1.9, §12).** Material lot → kit → part genealogy; CoC on file; receiving verification.
5. **Evidence mapping (the killer feature).** Each tracked record links to the AC7118 criterion(s) it satisfies; each criterion's "Compliant" status is **computed** from the presence + validity of its linked records, not a manual tick.

### 4.3 Secondary (post-MVP)
- Operator training/certification register (§4.5) with expiry; cold-storage temperature log (§6.1.1); tooling control (§7); additional scopes (MB, CP, LRP…).

### 4.4 Explicit non-goals (YAGNI)
- Not all 7 scopes / 30 sections in MVP — PAR hand-layup path only.
- No real QMS/ERP/historian integration; synthetic data.
- **No auto-disposition / no auto-NCR-closure** — a human signs.
- The LLM (if used) never decides compliance or computes a time limit.
- **Does not ship the verbatim AC7118 text** (copyright) — see §5.

---

## 5. Data & copyright guardrail (read carefully)

- **AC7118 is © Performance Review Institute.** Do **not** paste the document's verbatim criteria text into this public repo. Instead: reference criteria by **ID + a short paraphrased/representative title** (e.g., `5.1.12 — accumulated out-time/pot-life tracked to spec limits`), and design the app so a licensed user can **import their own AC7118 export privately** (gitignored) to populate full text. The demo ships ~20–30 **representative, paraphrased** criteria across the MVP sections — enough to show the mechanism without republishing the standard.
- **Synthetic shop data only:** a fictional composites shop, fictional prepreg/adhesive lots with invented out-time/shelf-life specs, fictional cure specs, parts, operators. Obviously synthetic; fixed seed. **No TAT/MSI data or IP, ever.**

---

## 6. Architecture & stack

Matches the portfolio's Django stack; deterministic compliance/time-math core with an optional, boxed-in LLM assist.

```
┌───────────────────────────────────────────────────────────────────┐
│  Browser — Readiness / Out-time / Cure / Traceability (Django+HTMX) │
│   • readiness dashboard (% by section, gaps, NCRs)                  │
│   • out-time gauges + freeze/thaw timeline; alerts                  │
│   • cure-cycle profile charts (Plotly) vs. spec window              │
│   • click any "ready" status → the evidence record + criterion      │
└───────────────▲───────────────────────────────┬───────────────────┘
                │                                 │
┌───────────────┴─────────────────────────────────▼───────────────────┐
│  Backend — Django + Postgres                                          │
│   compliance/  Criterion · CriterionStatus · NCR · EvidenceLink       │
│   materials/   MaterialLot · ColdStorageEvent · OutTimeEngine(det.)   │
│                · PotLife · ShelfLife · alerts                         │
│   cure/        CureRun · CureSpec · profile check (deterministic)     │
│   trace/       Lot→Kit→Part genealogy · CoC · receiving               │
│   readiness/   computes section readiness FROM evidence (not ticks)   │
│   assist/      OPTIONAL Claude: import criteria text → structured;    │
│                draft NCR explanation / readiness narrative (never     │
│                decides compliance or computes a limit)                │
│   data/        synthetic shop corpus (seeded) + paraphrased criteria  │
└──────────────────────────────────────────────────────────────────────┘
```

- **Backend:** Django + Postgres. **Charts:** Plotly (cure profiles, out-time gauges). **Frontend:** Django templates + HTMX.
- **Deterministic core (the trust + the substance):** out-time accrual, pot/shelf life, cure-window pass/fail, and readiness computation are plain tested Python — never an LLM.
- **Optional Claude assist** (only if `ANTHROPIC_API_KEY` set): ingest a user-supplied AC7118 export into structured criteria; draft NCR explanation text / a readiness summary. Always human-edited; never authoritative.
- **Packaging:** Docker · Python 3.12 · single `pyproject.toml` · **ruff + pytest** · GitHub Actions CI (matches the portfolio).

---

## 7. Compliance / process substance (get it right — you'll be asked)

- **Out-time engine:** out-time accrues **only while a lot is out of cold storage**; sum across multiple freeze/thaw cycles; compare to the material's spec limit; pot life starts at mix; shelf life is calendar-based from manufacture/recert. Alert thresholds (e.g., 80% / 90% / breach). Thaw-before-open (§5.1.15) and reseal-before-return (§5.1.13) are tracked checks.
- **Cure record:** capture §8.7.2 fields (facility, equipment ID, date/time start, part control/serial numbers) + the measured profile; deterministic pass/fail vs. the cure spec window (ramp rate, soak temp/time, pressure, vacuum); flag thermocouple/process-control-panel presence.
- **Readiness computation:** a criterion that's "demonstrated by data" is **Compliant only if** its linked evidence exists and is valid (e.g., §5.1.12 is green only if every active lot has a current, in-limit out-time record). Documentation-only criteria are manually attested **with** an uploaded procedure reference.
- **"Engineering takes precedence":** customer/engineering spec values override built-in defaults, and the app records which governed.

---

## 8. Definition of Done

- [ ] **App** deployed (public URL): seed the synthetic shop → readiness dashboard renders; open an out-time lot and watch an alert fire as it approaches the limit; open a cure run and see the profile vs. spec window pass/fail; click a "ready" criterion and land on its evidence record.
- [ ] **Evidence mapping works:** at least one criterion shows **NOT ready** specifically because a linked record is missing/expired (the thesis, demonstrated).
- [ ] **`README.md`** — what/why, one-command run, the **copyright + synthetic-data disclaimer**, links to demo + `DECISIONS.md` + (later) whiteboard.
- [ ] **`DECISIONS.md`** — §1 completed (rejected the tick-box checklist; accepted scoped-but-deep coverage).
- [ ] **Tests pass:** the deterministic out-time accrual (incl. multi-cycle), pot/shelf life, cure-window pass/fail, and the readiness-from-evidence computation (incl. "missing record → not ready").

---

## 9. Hosting / deployment
- Dockerized Django + Postgres on **Render** (via `render.yaml`), fronted by **Cloudflare**; planned subdomain `composite.hector-garza.com`.
- If the optional assist is enabled, `ANTHROPIC_API_KEY` is a Render secret — **never committed** (`.env` gitignored).

---

## 10. Repo bootstrap

```bash
mkdir composite-compliance-tracker && cd composite-compliance-tracker
cp /path/to/09-composite-compliance-tracker/SPEC.md .
cp /path/to/09-composite-compliance-tracker/PLAN.md .
# seed README.md, DECISIONS.md, WHITEBOARD-DRILL.md, .gitignore (python + .env), LICENSE (MIT)
git init && git add -A && git commit -m "chore: scaffold composite-compliance-tracker (spec + plan)"
git branch -M main
gh repo create cognitivefactory-hector/composite-compliance-tracker --public --source=. --remote=origin --push
```
> PUBLIC repo. **Never commit `ANTHROPIC_API_KEY`** or the verbatim AC7118 text. Synthetic data + paraphrased criteria only.

### `DECISIONS.md` starter
```markdown
# Decision Record — Composite Compliance Tracker

## Situation
<AC7118: ~30 sections, time-sensitive process data on paper/spreadsheets; missing: data↔criterion link + alerts before a limit blows>

## Decision
<readiness checklist + data tracking (out-time/cure/trace) with evidence mapping; deterministic time-math; REJECTED tick-box checklist, all-7-scopes MVP, LLM-decides-compliance>

## Risk
<silent out-time excursion; missing/unlinked record finding; alerts + deterministic math + traceable evidence + engineering-precedence; ACCEPTED scoped-but-deep coverage>

## Change
<live readiness vs. paper-chase; excursions prevented not discovered at MRB; every claim backed by a record>

## Whiteboard session
- Recording: <deferred — no mic yet>
- The "not ready because the record is missing" example: <…>
- Why deterministic math, not the LLM: <…>
```

---

## 11. Open questions to resolve in the plan
- Confirm MVP scope = PAR prepreg hand-layup (vs. another scope you care about).
- How many representative criteria to ship (target ~20–30 across §4/§5/§6/§8) and the paraphrase style.
- Whether to include the optional Claude assist in v1 or defer it (core is deterministic regardless).
- Out-time alert thresholds + whether accrual is event-based (in/out timestamps) or also supports a "still out" live clock.
