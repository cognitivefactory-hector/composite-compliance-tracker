"""Crown-jewel tests for the deterministic out-time engine (AC7118 §5.1.12).

Pure functions, no database — see tracker/materials/outtime.py.
"""
from datetime import UTC, datetime, timedelta

from tracker.materials.outtime import (
    AlertLevel,
    EventType,
    LimitSource,
    StorageEvent,
    accumulated_out_time,
    out_time_status,
    pot_life_remaining,
    resealed_before_return,
    resolve_out_time_limit,
    shelf_life_expired,
    thawed_before_open,
)


def _at(day: int, hour: int = 0) -> datetime:
    """A fixed UTC instant in Jan 2026, for readable timelines."""
    return datetime(2026, 1, day, hour, tzinfo=UTC)


def _removed(day: int, hour: int = 0) -> StorageEvent:
    return StorageEvent(EventType.REMOVED, _at(day, hour))


def _returned(day: int, hour: int = 0) -> StorageEvent:
    return StorageEvent(EventType.RETURNED, _at(day, hour))


def test_no_events_means_no_out_time():
    # A lot that was never removed from cold storage has accrued nothing.
    assert accumulated_out_time([], as_of=_at(10)) == timedelta(0)


def test_single_closed_interval_accrues_its_duration():
    events = [_removed(1, 8), _returned(1, 12)]  # out for 4 hours
    assert accumulated_out_time(events, as_of=_at(10)) == timedelta(hours=4)


def test_time_in_cold_storage_does_not_accrue():
    # Out 1->2 (24h), back in cold storage 2->5 (must NOT count), out 5->6 (24h).
    events = [_removed(1), _returned(2), _removed(5), _returned(6)]
    assert accumulated_out_time(events, as_of=_at(10)) == timedelta(hours=48)


def test_multi_cycle_accrual_sums_across_freeze_thaw_cycles():
    events = [
        _removed(1, 0), _returned(1, 6),    # 6h
        _removed(3, 0), _returned(3, 2),    # 2h
        _removed(8, 0), _returned(8, 10),   # 10h
    ]
    assert accumulated_out_time(events, as_of=_at(20)) == timedelta(hours=18)


def test_open_interval_accrues_to_as_of_live_clock():
    # Removed and not yet returned: out-time is a live clock up to `as_of`.
    events = [_removed(2, 0)]
    assert accumulated_out_time(events, as_of=_at(2, 9)) == timedelta(hours=9)


def test_events_are_sorted_before_pairing():
    # Out-of-order input must yield the same result as chronological input.
    events = [_returned(1, 12), _removed(1, 8)]
    assert accumulated_out_time(events, as_of=_at(10)) == timedelta(hours=4)


# --- Limit resolution: "engineering takes precedence" (AC7118 / SPEC §7) ---

def test_limit_defaults_to_material_spec_when_no_override():
    resolved = resolve_out_time_limit(default=timedelta(days=10), override=None)
    assert resolved.value == timedelta(days=10)
    assert resolved.source == LimitSource.DEFAULT


def test_engineering_override_takes_precedence_over_default():
    resolved = resolve_out_time_limit(
        default=timedelta(days=10), override=timedelta(days=6)
    )
    assert resolved.value == timedelta(days=6)
    assert resolved.source == LimitSource.ENGINEERING


# --- Alerting: thresholds at 80% / 90% / breach at the limit ---

LIMIT = timedelta(hours=100)  # round number → fraction == hours/100


def test_status_ok_below_warning_threshold():
    status = out_time_status(accumulated=timedelta(hours=50), limit=LIMIT)
    assert status.level == AlertLevel.OK
    assert status.fraction == 0.5
    assert status.remaining == timedelta(hours=50)


def test_status_warning_at_eighty_percent():
    status = out_time_status(accumulated=timedelta(hours=80), limit=LIMIT)
    assert status.level == AlertLevel.WARNING


def test_status_critical_at_ninety_percent():
    status = out_time_status(accumulated=timedelta(hours=90), limit=LIMIT)
    assert status.level == AlertLevel.CRITICAL


def test_status_breach_detected_exactly_at_the_limit():
    status = out_time_status(accumulated=timedelta(hours=100), limit=LIMIT)
    assert status.level == AlertLevel.BREACH
    assert status.remaining == timedelta(0)


def test_status_breach_past_limit_has_negative_remaining():
    status = out_time_status(accumulated=timedelta(hours=120), limit=LIMIT)
    assert status.level == AlertLevel.BREACH
    assert status.fraction == 1.2
    assert status.remaining == timedelta(hours=-20)


# --- Shelf life: calendar-based from manufacture/recert ---

def test_shelf_life_not_expired_before_expiration():
    assert shelf_life_expired(expiration=_at(30), as_of=_at(10)) is False


def test_shelf_life_expired_after_expiration():
    assert shelf_life_expired(expiration=_at(10), as_of=_at(30)) is True


def test_shelf_life_expired_exactly_at_expiration():
    # The instant it expires, the material is no longer usable.
    assert shelf_life_expired(expiration=_at(10), as_of=_at(10)) is True


# --- Pot life: starts at mix ---

def test_pot_life_remaining_before_it_expires():
    # Mixed at day 1 00:00, 8-hour pot life, checked at 03:00 → 5h left.
    remaining = pot_life_remaining(
        mixed_at=_at(1, 0), pot_life=timedelta(hours=8), as_of=_at(1, 3)
    )
    assert remaining == timedelta(hours=5)


def test_pot_life_remaining_is_negative_once_expired():
    remaining = pot_life_remaining(
        mixed_at=_at(1, 0), pot_life=timedelta(hours=8), as_of=_at(1, 10)
    )
    assert remaining == timedelta(hours=-2)


# --- Workflow checks: thaw-before-open (§5.1.15), reseal-before-return (§5.1.13) ---

def test_thawed_before_open_ok_when_thaw_precedes_open():
    assert thawed_before_open(thaw_completed=_at(1, 0), opened=_at(1, 2)) is True


def test_thawed_before_open_violation_when_opened_before_thaw():
    assert thawed_before_open(thaw_completed=_at(1, 5), opened=_at(1, 2)) is False


def test_resealed_before_return_ok_when_reseal_precedes_return():
    assert resealed_before_return(resealed=_at(2, 0), returned=_at(2, 1)) is True


def test_resealed_before_return_violation_when_returned_unsealed():
    assert resealed_before_return(resealed=None, returned=_at(2, 1)) is False
