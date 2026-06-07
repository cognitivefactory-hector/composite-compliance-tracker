# Whiteboard Drill — Composite Compliance Tracker (design-stage)

> Rehearsal for the recorded session (deferred — no mic; do it in writing now). **The push** is me playing tough reviewer; **Defense** is the position that survives; **⚠ Your move** is what only you can answer once you've built/measured it. Fold survivors into `DECISIONS.md`.
> Re-run a second drill after **M3** (readiness-from-evidence) with a real "missing-record → not ready" example.

## Q1 — "This is a checklist app — a fancy spreadsheet. Where's the engineering?"
**The push:** You rebuilt a tracking spreadsheet with a web UI.
**Defense (survives):** The engineering is the **evidence mapping + deterministic engines**: a criterion goes green only when its linked records exist and are valid (readiness is *computed*, not ticked), and the out-time/pot-life/cure-window math is tested code. AC7118 §4.4 literally audits spreadsheets *because* they're un-validated and un-linked — this is the opposite: traceable, tested, alerting.
**⚠ Your move:** Demo clicking a green status → its evidence record; that's the one-sentence proof.

## Q2 — "Out-time tracking is just subtraction. Why is it hard or valuable?"
**The push:** end − start. Trivial.
**Defense (survives):** It's **accumulated** out-time across multiple freeze/thaw cycles, accruing **only while out of cold storage**, against a **per-material spec limit** that engineering can override, with thaw-before-open and reseal-before-return rules — and the value is the **alert before breach**. Get it wrong and prepreg is used past its allowable life: a latent defect that scraps a part or escapes to a customer. That's the cost.
**⚠ Your move:** Put a number on the cost (scrap value / escape) from your experience.

## Q3 — "AC7118 has 7 scopes and 30 sections. You did one path — why be impressed?"
**The push:** You covered a sliver.
**Defense (survives):** Deliberate scoping: PAR hand-layup, done deep and correct, beats a shallow tick-box over all 7. The data model (criteria · evidence links · deterministic engines) generalizes to the other scopes; I'd rather ship one path an auditor would respect than thirty checkboxes nobody trusts.
**⚠ Your move:** Name which scope you'd add next and why.

## Q4 — "AC7118 §4.3/§4.4 means an auditor distrusts software and spreadsheets. How does your app pass its own standard?"
**The push:** Your tool is exactly what §4.4 flags.
**Defense (survives):** Validation (tested engines), an **audit trail**, **traceable evidence** behind every status, **human sign-off** (no auto-disposition), change control, and **"engineering takes precedence"** baked in. It's built to *be* the objective evidence, not to replace the engineer's judgment.
**⚠ Your move:** From your audits, name the specific software-control expectation (§4.3) this satisfies.

## Q5 — "Synthetic data, not a real accredited shop — why believe it?"
**The push:** It's a toy.
**Defense (survives):** The criteria are public and the data model reflects the real controls (out-time, cure, lot genealogy). First real-data validation: load a real shop's lot/cure records and confirm the readiness computation matches their audit reality. Synthetic proves the mechanism, honestly.
**⚠ Your move:** Note what's hardest in real shop data (paper records, inconsistent lot IDs).

## Q6 — "Show me a status the app flagged NOT ready that a human would've ticked 'yes.'"
**The push:** Where's the judgment?
**Defense (survives):** A criterion (e.g., §5.1.12) shows **NOT ready** because an active lot's out-time record is missing or expired — something a human eyeballing a binder would mark "yes, we track that." Data-backed readiness catches the unbacked claim. That's the whole thesis.
**⚠ Your move:** Build the seed so one lot is expired / one record missing — so this example is real on screen.

## Verdict — SDRC after the drill
- **Holds:** evidence-computed readiness; deterministic time-math; scoped-but-deep; engineering-precedence.
- **Sharpen:** lead with **Q1** (evidence mapping) and **Q6** (the not-ready-because-missing example); put a cost number on Q2.
- **Land this line:** *"A green status here isn't someone's checkbox — it's a live, in-limit record the auditor can click straight to."*
