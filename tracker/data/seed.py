"""Build a fictional, obviously-synthetic composites shop for the demo.

Deterministic given ``now`` (tests pass a fixed instant); the management command
uses the real clock so the near-breach lot is genuinely near breach when viewed.
States are crafted to make the thesis visible: §5.1.12 is NOT ready because an
active lot's shelf life has expired, one lot is firing an out-time alert near
(but under) its limit, the cure criterion is fully evidence-backed, and the
documentation criteria are a realistic mix of attested / gap / NA.

NO employer data, NO verbatim AC7118 text — paraphrased criteria only.
"""
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from tracker.compliance.models import NCR, Criterion, CriterionStatus, EvidenceLink
from tracker.cure.models import CureRun, CureSpec
from tracker.materials.models import ColdStorageEvent, Material, MaterialLot
from tracker.trace.models import Kit, Part

from . import criteria_repr

# Documentation criteria the fictional shop has NOT yet attested → GAP.
_DOC_GAPS = {"4.2.1", "6.2.1", "7.1.1", "5.1.20"}
# Criteria not applicable to the PAR prepreg hand-layup path → NA (explained).
_NA = {
    "9.1.1": "No liquid resin moulding on the PAR prepreg hand-layup path.",
    "10.1.1": "No metal bonding performed in this scope.",
    "11.1.1": "No honeycomb core processing in this scope.",
}

# A fully in-window 177 C cure profile (minute, temp C, pressure psi, vacuum inHg).
_PASS_PROFILE = [
    {"minute": 0, "temperature": 20, "pressure": 90, "vacuum": 25},
    {"minute": 60, "temperature": 140, "pressure": 90, "vacuum": 25},
    {"minute": 90, "temperature": 177, "pressure": 90, "vacuum": 25},
    {"minute": 215, "temperature": 177, "pressure": 90, "vacuum": 25},
    {"minute": 245, "temperature": 100, "pressure": 90, "vacuum": 25},
]


def _clear() -> None:
    Part.objects.all().delete()
    Kit.objects.all().delete()
    EvidenceLink.objects.all().delete()
    NCR.objects.all().delete()
    CriterionStatus.objects.all().delete()
    Criterion.objects.all().delete()
    CureRun.objects.all().delete()
    CureSpec.objects.all().delete()
    ColdStorageEvent.objects.all().delete()
    MaterialLot.objects.all().delete()
    Material.objects.all().delete()


def _seed_materials_and_lots(now: datetime) -> dict[str, MaterialLot]:
    prepreg = Material.objects.create(
        name="Hexcel 8552/IM7 prepreg",
        kind=Material.Kind.PREPREG,
        default_out_time_limit=timedelta(days=30),
    )
    adhesive = Material.objects.create(
        name="FM 300 film adhesive",
        kind=Material.Kind.ADHESIVE,
        default_out_time_limit=timedelta(days=20),
    )

    lots: dict[str, MaterialLot] = {}

    # Healthy prepreg lot — a couple of short cycles, shelf life well in date.
    healthy = MaterialLot.objects.create(
        material=prepreg,
        lot_number="HX-1001",
        manufactured_at=now - timedelta(days=150),
        expiration=now + timedelta(days=120),
    )
    _cycle(healthy, now - timedelta(days=40), timedelta(hours=6))
    _cycle(healthy, now - timedelta(days=12), timedelta(hours=8))
    lots["healthy_prepreg"] = healthy

    # Healthy adhesive lot.
    healthy_adh = MaterialLot.objects.create(
        material=adhesive,
        lot_number="FM-2001",
        manufactured_at=now - timedelta(days=100),
        expiration=now + timedelta(days=150),
    )
    _cycle(healthy_adh, now - timedelta(days=20), timedelta(hours=5))
    lots["healthy_adhesive"] = healthy_adh

    # Near-breach lot — removed and still out, ~92% of the 30-day limit.
    near = MaterialLot.objects.create(
        material=prepreg,
        lot_number="HX-1002",
        manufactured_at=now - timedelta(days=60),
        expiration=now + timedelta(days=60),
    )
    ColdStorageEvent.objects.create(
        lot=near,
        event_type="removed",
        occurred_at=now - timedelta(days=27, hours=14),  # ~27.6d out → ~92%
    )
    lots["near_breach"] = near

    # Expired lot — shelf life lapsed; drives §5.1.12 to NOT ready.
    expired = MaterialLot.objects.create(
        material=prepreg,
        lot_number="HX-0900",
        manufactured_at=now - timedelta(days=200),
        expiration=now - timedelta(days=5),
    )
    _cycle(expired, now - timedelta(days=30), timedelta(hours=4))
    lots["expired"] = expired

    return lots


def _cycle(lot: MaterialLot, removed_at: datetime, duration: timedelta) -> None:
    ColdStorageEvent.objects.create(lot=lot, event_type="removed", occurred_at=removed_at)
    ColdStorageEvent.objects.create(
        lot=lot, event_type="returned", occurred_at=removed_at + duration
    )


def _seed_cure(now: datetime) -> list[CureRun]:
    spec = CureSpec.objects.create(
        name="177 C / 350 F prepreg cure",
        soak_temp_min=171.0,
        soak_temp_max=183.0,
        soak_min_duration=timedelta(minutes=120),
        ramp_rate_min=1.0,
        ramp_rate_max=3.0,
        pressure_min=85.0,
        pressure_max=100.0,
        vacuum_min=22.0,
    )
    runs = []
    for i, (offset, serials) in enumerate(
        [(30, ["PN-1001", "PN-1002"]), (10, ["PN-1003"])], start=1
    ):
        runs.append(
            CureRun.objects.create(
                spec=spec,
                facility="Plant 1 — Autoclave Bay",
                equipment_id=f"AUTOCLAVE-{i}",
                started_at=now - timedelta(days=offset),
                part_serials=serials,
                thermocouple_present=True,
                process_panel_present=True,
                profile=_PASS_PROFILE,
            )
        )
    return runs


def _seed_criteria(now: datetime) -> dict[str, Criterion]:
    criteria: dict[str, Criterion] = {}
    for spec in criteria_repr.CRITERIA:
        criterion = Criterion.objects.create(
            criterion_id=spec.criterion_id,
            title=spec.title,
            section=spec.section,
            scope=spec.scope,
            evidence_type=spec.evidence_type,
        )
        criteria[spec.criterion_id] = criterion

        if spec.criterion_id in _NA:
            CriterionStatus.objects.create(
                criterion=criterion,
                is_na=True,
                na_explanation=_NA[spec.criterion_id],
            )
        elif spec.evidence_type == criteria_repr.DOCUMENTATION:
            if spec.criterion_id not in _DOC_GAPS:
                # Attested documentation criterion → COMPLIANT.
                CriterionStatus.objects.create(
                    criterion=criterion,
                    procedure_reference=f"QOP-{spec.criterion_id}",
                    attested=True,
                    signed_by="J. Quality (synthetic)",
                    signed_at=now - timedelta(days=14),
                )
            # _DOC_GAPS get no status → documentation readiness is a GAP.
    return criteria


def _seed_genealogy(
    now: datetime, lots: dict[str, MaterialLot], runs: list[CureRun]
) -> None:
    """Build a lot -> kit -> part -> cure genealogy from the healthy prepreg lot."""
    kit = Kit.objects.create(kit_number="KIT-3007", created_at=now - timedelta(days=35))
    kit.lots.add(lots["healthy_prepreg"], lots["healthy_adhesive"])
    for serial in ("PN-1001", "PN-1002"):
        Part.objects.create(
            part_number="SKIN-LH-OUTBD",
            serial=serial,
            kit=kit,
            cure_run=runs[0] if runs else None,
        )


@transaction.atomic
def seed(now: datetime | None = None) -> dict[str, int]:
    """Reset and populate the synthetic shop. Returns a summary of counts."""
    now = now or timezone.now()
    _clear()

    lots = _seed_materials_and_lots(now)
    runs = _seed_cure(now)
    criteria = _seed_criteria(now)
    _seed_genealogy(now, lots, runs)

    # Wire explicit evidence links so a status can be clicked through to a record.
    c_out_time = criteria["5.1.12"]
    for lot in lots.values():
        EvidenceLink.objects.create(criterion=c_out_time, record=lot)
    c_cure = criteria["8.7.2"]
    for run in runs:
        EvidenceLink.objects.create(criterion=c_cure, record=run)

    # A negative finding gets an NCR — opened, never auto-closed.
    NCR.open_for(
        c_out_time,
        description=(
            f"Lot {lots['expired'].lot_number} shelf life expired; §5.1.12 cannot "
            "be demonstrated until the lot is dispositioned."
        ),
    )

    return {
        "materials": Material.objects.count(),
        "lots": MaterialLot.objects.count(),
        "cure_specs": CureSpec.objects.count(),
        "cure_runs": CureRun.objects.count(),
        "criteria": Criterion.objects.count(),
        "ncrs": NCR.objects.count(),
        "kits": Kit.objects.count(),
        "parts": Part.objects.count(),
    }
