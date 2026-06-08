"""DB-level tests: readiness computed from real records, NA/NCR rules.

The headline: a criterion backed by an expired/missing record computes NOT ready
— it is never auto-green.
"""
from datetime import UTC, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError

from tracker.compliance.models import NCR, Criterion, CriterionStatus
from tracker.materials.models import Material, MaterialLot
from tracker.readiness.engine import Readiness
from tracker.readiness.evaluate import evaluate_criterion

pytestmark = pytest.mark.django_db

_AS_OF = datetime(2026, 3, 1, tzinfo=UTC)


def _out_time_criterion() -> Criterion:
    return Criterion.objects.create(
        criterion_id="5.1.12",
        title="Accumulated out-time / pot-life tracked to spec limits",
        section="5.1",
        scope="PAR",
        evidence_type=Criterion.EvidenceType.OUT_TIME,
    )


def _lot(*, expiration: datetime, with_event: bool = True) -> MaterialLot:
    material = Material.objects.create(
        name="Hexcel 8552",
        kind="prepreg",
        default_out_time_limit=timedelta(days=30),
    )
    lot = MaterialLot.objects.create(
        material=material,
        lot_number="LOT-X",
        manufactured_at=datetime(2026, 1, 1, tzinfo=UTC),
        expiration=expiration,
    )
    if with_event:
        lot.storage_events.create(
            event_type="removed", occurred_at=datetime(2026, 2, 1, tzinfo=UTC)
        )
        lot.storage_events.create(
            event_type="returned", occurred_at=datetime(2026, 2, 1, 4, tzinfo=UTC)
        )
    return lot


def test_criterion_with_expired_lot_computes_not_ready():
    # THE THESIS: shelf life already expired → §5.1.12 is a GAP, not green.
    criterion = _out_time_criterion()
    _lot(expiration=datetime(2026, 2, 1, tzinfo=UTC))  # expired before _AS_OF
    result = evaluate_criterion(criterion, as_of=_AS_OF)
    assert result.status == Readiness.GAP


def test_criterion_with_missing_record_computes_not_ready():
    # An active lot with no logged out-time record at all → GAP.
    criterion = _out_time_criterion()
    _lot(expiration=datetime(2026, 12, 1, tzinfo=UTC), with_event=False)
    result = evaluate_criterion(criterion, as_of=_AS_OF)
    assert result.status == Readiness.GAP


def test_criterion_with_valid_lot_is_compliant():
    criterion = _out_time_criterion()
    _lot(expiration=datetime(2026, 12, 1, tzinfo=UTC), with_event=True)
    result = evaluate_criterion(criterion, as_of=_AS_OF)
    assert result.status == Readiness.COMPLIANT


def test_retired_lot_is_excluded_from_evidence():
    criterion = _out_time_criterion()
    lot = _lot(expiration=datetime(2026, 2, 1, tzinfo=UTC))  # expired
    lot.is_active = False
    lot.save()
    # The only lot is retired → no active evidence → GAP (not COMPLIANT).
    result = evaluate_criterion(criterion, as_of=_AS_OF)
    assert result.status == Readiness.GAP


def test_criterion_marked_na_with_explanation_computes_na():
    criterion = Criterion.objects.create(
        criterion_id="9.1.1",
        title="Liquid resin process controls",
        section="9.1",
        scope="PAR",
        evidence_type=Criterion.EvidenceType.DOCUMENTATION,
    )
    CriterionStatus.objects.create(
        criterion=criterion, is_na=True, na_explanation="No liquid resin on this path"
    )
    result = evaluate_criterion(criterion, as_of=_AS_OF)
    assert result.status == Readiness.NA


def test_na_without_explanation_is_invalid():
    criterion = _out_time_criterion()
    status = CriterionStatus(criterion=criterion, is_na=True, na_explanation="")
    with pytest.raises(ValidationError):
        status.full_clean()


def test_opening_an_ncr_creates_a_linked_open_record():
    criterion = _out_time_criterion()
    ncr = NCR.open_for(criterion, description="Lot LOT-X out-time record missing")
    assert ncr.criterion == criterion
    assert ncr.is_closed is False
    assert criterion.ncrs.count() == 1
