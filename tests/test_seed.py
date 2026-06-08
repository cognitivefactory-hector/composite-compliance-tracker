"""Tests for the synthetic shop seed (AC7118 demo corpus).

A fixed `now` makes the seeded states deterministic.
"""
from datetime import UTC, datetime

import pytest

from tracker.compliance.models import NCR, Criterion
from tracker.data.criteria_repr import CRITERIA
from tracker.data.seed import seed
from tracker.materials.models import MaterialLot
from tracker.materials.outtime import AlertLevel
from tracker.readiness.engine import Readiness
from tracker.readiness.evaluate import evaluate_criterion

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 6, 1, tzinfo=UTC)


def test_seed_loads_full_criteria_catalog():
    seed(now=NOW)
    assert Criterion.objects.count() == len(CRITERIA)


def test_seed_is_idempotent():
    seed(now=NOW)
    seed(now=NOW)
    assert Criterion.objects.count() == len(CRITERIA)
    assert MaterialLot.objects.count() == 4


def test_out_time_criterion_is_not_ready_because_of_an_expired_lot():
    # The thesis, on screen: §5.1.12 is GAP because an active lot is expired.
    seed(now=NOW)
    criterion = Criterion.objects.get(criterion_id="5.1.12")
    result = evaluate_criterion(criterion, as_of=NOW)
    assert result.status == Readiness.GAP
    assert result.evidence_ids  # points at the offending lot(s)


def test_seed_has_a_lot_near_breach_but_none_breached():
    seed(now=NOW)
    levels = {
        lot.out_time_status(NOW).level
        for lot in MaterialLot.objects.filter(is_active=True)
    }
    assert AlertLevel.CRITICAL in levels  # an alert is firing
    assert AlertLevel.BREACH not in levels  # near the limit, not over it


def test_cure_criterion_is_compliant():
    seed(now=NOW)
    criterion = Criterion.objects.get(criterion_id="8.7.2")
    assert evaluate_criterion(criterion, as_of=NOW).status == Readiness.COMPLIANT


def test_seed_produces_a_realistic_mix_of_statuses():
    seed(now=NOW)
    statuses = {
        evaluate_criterion(c, as_of=NOW).status for c in Criterion.objects.all()
    }
    assert Readiness.COMPLIANT in statuses
    assert Readiness.GAP in statuses
    assert Readiness.NA in statuses


def test_seed_opens_at_least_one_ncr():
    seed(now=NOW)
    assert NCR.objects.filter(is_closed=False).exists()
