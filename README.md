# Composite Compliance Tracker

A NADCAP **AC7118 (Composites)** audit-readiness + process-data tracker. It logs the time-sensitive controls a composites shop lives or dies by — prepreg **out-time**, **cure cycles**, lot traceability — and **maps every record to the AC7118 criterion it provides objective evidence for**, so audit readiness is *computed from data*, not self-attested on a checklist.

> ⚠️ **Illustrative tool on synthetic data — not a quality system of record; a qualified person dispositions and signs.** No employer data, ever. It **does not republish the copyrighted AC7118 text** (© Performance Review Institute) — it references criteria by ID + paraphrased titles and lets a licensed user import the real text privately.

![Readiness dashboard](docs/dashboard.png)

---

## The thesis — readiness computed from evidence, not ticked

A green status here isn't someone's checkbox — it's a **live, in-limit record an auditor can click straight to**. A criterion turns compliant *only* when its linked records exist and are valid; the moment a record goes missing, expires, or breaches a limit, the criterion computes **NOT ready** — no human can quietly tick "yes, we track that."

Below, §5.1.12 is **not ready** because an active prepreg lot's shelf life has expired. The app names the offending lot ("⚠ blocks readiness"), opens an NCR, and links straight to the record — while a separate lot fires a 92% out-time alert *before* it breaches.

![Criterion §5.1.12 — not ready because a record is expired](docs/criterion-5112.png)

This is the hireable signal: anyone can build a checklist UI; the engineering is the **link between live process data and the requirement it satisfies**, plus deterministic, tested time-math that an auditor (and a hiring manager) can trust.

---

## What it does (MVP scope: PAR prepreg hand-layup)

- **AC7118 readiness checklist** — ~24 paraphrased criteria across §4/§5/§6/§7/§8/§12, each **Compliant / Gap / NA-explained**, with NCRs for negatives and a dashboard (% ready by section, open gaps, open NCRs).
- **Out-time / shelf-life / pot-life tracker** (flagship → §5.1.12) — per lot: freeze/thaw events, **accumulated out-time across cycles** (accrues only while out of cold storage), shelf/pot life, per-material limits with **engineering override**, and **proactive alerts before a limit is blown**.
- **Cure-cycle records** (→ §8.7.2) — facility, equipment, date/time, part serials, and the time/temp/pressure/vacuum profile vs. the cure-spec window (deterministic pass/fail) on a Plotly chart.
- **Lot / kit / part traceability** (→ §5.1.5/§12) — lot → kit → part → cure genealogy.
- **Evidence mapping** (the killer feature) — a criterion goes green only when its linked records exist and are valid. Click a status → land on the proof.
- **Optional Claude assist** (gated on `ANTHROPIC_API_KEY`) — drafts NCR/readiness text and structures a licensed criteria import; **advisory only, never decides compliance or computes a limit.**

| Out-time gauge & freeze/thaw timeline | Cure profile vs. spec window |
| --- | --- |
| ![Lot out-time](docs/lot-out-time.png) | ![Cure profile](docs/cure-profile.png) |

---

## Quick start (one command)

```bash
docker compose up --build
```

Then open **http://localhost:8000** — the synthetic shop is seeded on startup, so the readiness dashboard renders immediately. Try:

1. The **dashboard** — note the firing out-time alert on lot `HX-1002`.
2. Click into **§5.1.12** — it's a gap *because* lot `HX-0900` is expired; follow the link to the lot.
3. Open a **cure run** — see the measured profile vs. the soak window, pass/fail per criterion.
4. With `ANTHROPIC_API_KEY` set, a gap criterion shows a **"Draft NCR explanation"** button.

To reseed manually: `docker compose exec web python manage.py seed_shop`.

---

## Tech stack

- **Backend:** Django 5 + Postgres · **Charts:** Plotly · **Frontend:** Django templates + HTMX
- **Deterministic core** (out-time accrual, pot/shelf life, cure-window, readiness-from-evidence) — plain, tested Python; **never an LLM**
- **Packaging:** Docker · Python 3.12 · single `pyproject.toml` · **Quality:** pytest + ruff + GitHub Actions CI

### Architecture

```
tracker/
  materials/   MaterialLot · ColdStorageEvent · outtime.py   (deterministic out-time engine)
  cure/        CureSpec · CureRun · window.py · charts.py     (deterministic cure-window check)
  compliance/  Criterion · CriterionStatus · EvidenceLink · NCR
  readiness/   engine.py (pure) + evaluate.py                 (computes status FROM evidence)
  trace/       Kit · Part                                     (lot→kit→part genealogy)
  assist/      client.py · prompts.py                         (optional, gated, advisory)
  data/        seed.py · criteria_repr.py                     (synthetic shop + paraphrased criteria)
```

The engines are pure functions over explicit timestamps (no hidden clock), so every safety-relevant calculation is reproducible and test-first. See [`SPEC.md`](./SPEC.md) §6–7.

---

## Testing

```bash
pip install -e .[dev]
# Tests need Postgres; point DATABASE_URL at one (the Claude assist is always mocked):
DATABASE_URL=postgres://postgres:postgres@localhost:5432/composite_test pytest
ruff check .
```

CI (GitHub Actions) runs `ruff` + `pytest` against a Postgres service on every push/PR. The crown-jewel tests cover multi-cycle out-time accrual + engineering override, cure-window pass/fail, and the readiness thesis — **"missing record → not ready."**

---

## Deploy (Render)

The repo ships a [`render.yaml`](./render.yaml) Blueprint (Dockerized web service + Postgres, `/healthz` health check, `SEED_ON_START=true` so the public demo is never empty).

1. On Render: **New → Blueprint**, connect this repo. It provisions the web service + a Basic Postgres (a workspace allows only one *free* Postgres and free instances expire after 30 days, so the Blueprint uses a small paid tier for a persistent demo) and generates `DJANGO_SECRET_KEY`.
2. Optional: set `ANTHROPIC_API_KEY` in the dashboard to enable the Claude assist.
3. Optional custom domain (`composite.hector-garza.com`): add it in Render and uncomment `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` in `render.yaml`. (`RENDER_EXTERNAL_HOSTNAME` is trusted automatically.)

Secrets are never committed — `.env` is gitignored.

---

## Links

- 🔗 **Live demo:** https://composite-compliance-tracker.onrender.com
- 🧠 **Decision record:** [`DECISIONS.md`](./DECISIONS.md) — why readiness is computed from data, the rejected tick-box checklist, the accepted scoped-but-deep coverage
- 📋 **Spec & plan:** [`SPEC.md`](./SPEC.md) · [`PLAN.md`](./PLAN.md)
- 🎥 **Whiteboard walkthrough:** _deferred (no mic yet) — `DECISIONS.md` carries the judgment for now_

Part of [hector-garza.com](https://hector-garza.com)'s portfolio. One of three equal deliverables: the app, the decision record, and a recorded design defense — because a working demo no longer proves competence; the judgment behind it does.

---

## License

MIT — see [`LICENSE`](./LICENSE). Synthetic data and paraphrased criteria only; the AC7118 standard itself is © Performance Review Institute and is not included.
