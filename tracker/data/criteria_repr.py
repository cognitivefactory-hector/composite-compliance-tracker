"""Representative, PARAPHRASED AC7118 criteria — the demo catalog.

NOT the verbatim © Performance Review Institute text. Each entry references a
criterion by ID and a short, paraphrased title only. A licensed user imports the
real text privately (see private_criteria/ in .gitignore). ~24 criteria across
§4/§5/§6/§7/§8/§9/§10/§11/§12, scoped to the PAR prepreg hand-layup path.
"""
from dataclasses import dataclass

# Evidence-type values mirror tracker.compliance.models.Criterion.EvidenceType.
OUT_TIME = "out_time"
CURE = "cure"
DOCUMENTATION = "documentation"


@dataclass(frozen=True)
class CriterionSpec:
    criterion_id: str
    title: str  # paraphrased / representative
    section: str
    evidence_type: str
    scope: str = "PAR"


CRITERIA: tuple[CriterionSpec, ...] = (
    # § 4 — Quality system & records
    CriterionSpec("4.1.1", "Quality manual addresses the AC7118 scope", "4.1", DOCUMENTATION),
    CriterionSpec("4.2.1", "Internal audit schedule maintained and followed", "4.2", DOCUMENTATION),
    CriterionSpec("4.3.1", "Software/spreadsheet tools validated and access-controlled", "4.3", DOCUMENTATION),
    CriterionSpec("4.4.1", "Spreadsheets used as quality records are themselves controlled", "4.4", DOCUMENTATION),
    CriterionSpec("4.5.1", "Operator training/certification current for the process", "4.5", DOCUMENTATION),
    # § 5 — Material control
    CriterionSpec("5.1.1", "Only approved materials from the AML are used", "5.1", DOCUMENTATION),
    CriterionSpec("5.1.5", "Incoming material lot traceability to CoC maintained", "5.1", DOCUMENTATION),
    CriterionSpec("5.1.9", "Certificate of conformance on file for each lot", "5.1", DOCUMENTATION),
    CriterionSpec("5.1.12", "Accumulated out-time / pot-life tracked to spec limits", "5.1", OUT_TIME),
    CriterionSpec("5.1.13", "Material resealed before return to cold storage", "5.1", DOCUMENTATION),
    CriterionSpec("5.1.15", "Material thawed to ambient before opening", "5.1", DOCUMENTATION),
    CriterionSpec("5.1.20", "Expired material quarantined and dispositioned", "5.1", DOCUMENTATION),
    # § 6 — Storage & environment
    CriterionSpec("6.1.1", "Cold-storage temperature continuously monitored and logged", "6.1", DOCUMENTATION),
    CriterionSpec("6.2.1", "Work-area temperature/humidity controlled and recorded", "6.2", DOCUMENTATION),
    # § 7 — Tooling
    CriterionSpec("7.1.1", "Layup tooling controlled and uniquely identified", "7.1", DOCUMENTATION),
    # § 8 — Process control & cure
    CriterionSpec("8.1.1", "Cure performed to an approved cure specification", "8.1", DOCUMENTATION),
    CriterionSpec("8.7.2", "Cure-cycle records capture facility, equipment, time, serials, profile", "8.7", CURE),
    CriterionSpec("8.7.4", "Thermocouple placement recorded for each cure", "8.7", DOCUMENTATION),
    CriterionSpec("8.8.1", "Autoclave/oven calibrated and within calibration date", "8.8", DOCUMENTATION),
    # § 12 — Traceability
    CriterionSpec("12.1.1", "Material lot -> kit -> part genealogy maintained", "12.1", DOCUMENTATION),
    # Other scopes — not applicable to the PAR prepreg hand-layup path
    CriterionSpec("9.1.1", "Liquid resin processing controls", "9.1", DOCUMENTATION),
    CriterionSpec("10.1.1", "Metal bond surface-preparation controls", "10.1", DOCUMENTATION),
    CriterionSpec("11.1.1", "Honeycomb core processing controls", "11.1", DOCUMENTATION),
)
