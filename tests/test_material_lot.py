"""Model-level tests: MaterialLot wires its stored events into the pure engine."""
from datetime import UTC, datetime, timedelta

import pytest

from tracker.materials.models import Material, MaterialLot
from tracker.materials.outtime import AlertLevel, EventType, LimitSource

pytestmark = pytest.mark.django_db


_BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _dt(day: int, hour: int = 0) -> datetime:
    # Offset from 2026-01-01 so day numbers beyond a month's length are valid.
    return _BASE + timedelta(days=day - 1, hours=hour)


def _make_lot(**overrides) -> MaterialLot:
    material = Material.objects.create(
        name="Hexcel 8552 prepreg",
        kind="prepreg",
        default_out_time_limit=timedelta(days=10),
    )
    fields = dict(
        material=material,
        lot_number="LOT-001",
        manufactured_at=_dt(1),
        expiration=_dt(100),
    )
    fields.update(overrides)
    return MaterialLot.objects.create(**fields)


def test_lot_accumulates_out_time_from_its_storage_events():
    lot = _make_lot()
    lot.storage_events.create(event_type=EventType.REMOVED, occurred_at=_dt(2, 0))
    lot.storage_events.create(event_type=EventType.RETURNED, occurred_at=_dt(2, 6))
    assert lot.accumulated_out_time(as_of=_dt(20)) == timedelta(hours=6)


def test_lot_resolved_limit_defaults_to_material_spec():
    lot = _make_lot()
    resolved = lot.resolved_out_time_limit()
    assert resolved.value == timedelta(days=10)
    assert resolved.source == LimitSource.DEFAULT


def test_lot_engineering_override_takes_precedence():
    lot = _make_lot(out_time_limit_override=timedelta(days=6))
    resolved = lot.resolved_out_time_limit()
    assert resolved.value == timedelta(days=6)
    assert resolved.source == LimitSource.ENGINEERING


def test_lot_out_time_status_uses_resolved_limit():
    # Default 10-day limit; left out 9 days → 90% → CRITICAL.
    lot = _make_lot()
    lot.storage_events.create(event_type=EventType.REMOVED, occurred_at=_dt(1, 0))
    status = lot.out_time_status(as_of=_dt(10, 0))
    assert status.level == AlertLevel.CRITICAL


def test_lot_shelf_life_expired_flag_from_expiration():
    lot = _make_lot(expiration=_dt(5))
    assert lot.shelf_life_expired(as_of=_dt(10)) is True
    assert _make_lot(expiration=_dt(50)).shelf_life_expired(as_of=_dt(10)) is False
