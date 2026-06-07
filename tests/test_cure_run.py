"""Model-level tests: CureRun wires its stored profile into the pure engine
and flags missing AC7118 §8.7.2 record fields."""
from datetime import UTC, datetime, timedelta

import pytest

from tracker.cure.models import CureRun, CureSpec

pytestmark = pytest.mark.django_db


def _make_spec() -> CureSpec:
    return CureSpec.objects.create(
        name="177C/350F prepreg cure",
        soak_temp_min=171.0,
        soak_temp_max=183.0,
        soak_min_duration=timedelta(minutes=120),
        ramp_rate_min=1.0,
        ramp_rate_max=3.0,
        pressure_min=85.0,
        pressure_max=100.0,
        vacuum_min=22.0,
    )


def _profile(samples):
    return [
        {"minute": m, "temperature": t, "pressure": p, "vacuum": v}
        for (m, t, p, v) in samples
    ]


_PASSING = _profile(
    [
        (0, 20, 90, 25),
        (60, 140, 90, 25),
        (90, 177, 90, 25),
        (215, 177, 90, 25),
        (245, 100, 90, 25),
    ]
)


def _make_run(spec, **overrides) -> CureRun:
    fields = dict(
        spec=spec,
        facility="Plant 1",
        equipment_id="AUTOCLAVE-3",
        started_at=datetime(2026, 2, 1, 8, tzinfo=UTC),
        part_serials=["PN-1001", "PN-1002"],
        thermocouple_present=True,
        process_panel_present=True,
        profile=_PASSING,
    )
    fields.update(overrides)
    return CureRun.objects.create(**fields)


def test_cure_run_in_window_profile_passes():
    run = _make_run(_make_spec())
    result = run.evaluate()
    assert result.passed is True


def test_cure_run_out_of_window_profile_fails():
    bad = _profile([(0, 20, 90, 25), (30, 140, 90, 25), (60, 177, 90, 25),
                    (185, 177, 90, 25), (215, 100, 90, 25)])  # ramp 4 C/min
    run = _make_run(_make_spec(), profile=bad)
    result = run.evaluate()
    assert result.passed is False
    assert result.check("ramp_rate").passed is False


def test_missing_required_field_is_flagged():
    run = _make_run(_make_spec(), part_serials=[], facility="")
    missing = run.missing_required_fields()
    assert "part_serials" in missing
    assert "facility" in missing


def test_complete_run_has_no_missing_required_fields():
    run = _make_run(_make_spec())
    assert run.missing_required_fields() == []
