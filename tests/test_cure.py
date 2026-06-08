"""Crown-jewel tests for the deterministic cure-window engine (AC7118 §8.7.2).

Pure functions, no database — see tracker/cure/window.py. The spec window below
mirrors a representative 177 C / 350 F prepreg cure.
"""
from datetime import timedelta

from tracker.cure.window import (
    CureWindow,
    ProfileSample,
    evaluate_cure,
)

WINDOW = CureWindow(
    soak_temp_min=171.0,
    soak_temp_max=183.0,
    soak_min_duration=timedelta(minutes=120),
    ramp_rate_min=1.0,
    ramp_rate_max=3.0,
    pressure_min=85.0,
    pressure_max=100.0,
    vacuum_min=22.0,
)


def _s(minute: float, temp: float, pressure: float = 90.0, vacuum: float = 25.0):
    return ProfileSample(
        elapsed=timedelta(minutes=minute),
        temperature=temp,
        pressure=pressure,
        vacuum=vacuum,
    )


# A fully in-window cure: ramp ~1-2 C/min, soak 177 C for 125 min, then cool.
def _passing_profile():
    return [
        _s(0, 20),
        _s(60, 140),   # ramp 2.0 C/min
        _s(90, 177),   # ramp ~1.23 C/min into the soak band
        _s(215, 177),  # soak in-band 90->215 = 125 min
        _s(245, 100),  # cooldown (decreasing temp, not a ramp-up segment)
    ]


def test_fully_in_window_profile_passes():
    result = evaluate_cure(WINDOW, _passing_profile())
    assert result.passed is True
    assert all(c.passed for c in result.checks)


def test_ramp_too_fast_fails():
    profile = [_s(0, 20), _s(30, 140), _s(60, 177), _s(185, 177), _s(215, 100)]
    result = evaluate_cure(WINDOW, profile)  # 0->30: 4.0 C/min, over max
    assert result.passed is False
    assert result.check("ramp_rate").passed is False


def test_soak_too_short_fails():
    # In-band only 90 minutes (177 from t=90 to t=180), below the 120-min minimum.
    profile = [_s(0, 20), _s(60, 140), _s(90, 177), _s(180, 177), _s(210, 100)]
    result = evaluate_cure(WINDOW, profile)
    assert result.passed is False
    assert result.check("soak_duration").passed is False


def test_overtemp_above_soak_max_fails():
    profile = [_s(0, 20), _s(60, 140), _s(90, 177), _s(150, 190), _s(215, 177), _s(245, 100)]
    result = evaluate_cure(WINDOW, profile)  # 190 C exceeds soak_temp_max 183
    assert result.passed is False
    assert result.check("overtemp").passed is False


def test_low_vacuum_during_soak_fails():
    profile = [_s(0, 20), _s(60, 140), _s(90, 177), _s(215, 177, vacuum=15.0), _s(245, 100)]
    result = evaluate_cure(WINDOW, profile)
    assert result.passed is False
    assert result.check("vacuum").passed is False


def test_low_pressure_during_soak_fails():
    profile = [
        _s(0, 20),
        _s(60, 140),
        _s(90, 177, pressure=70.0),
        _s(215, 177, pressure=70.0),
        _s(245, 100),
    ]
    result = evaluate_cure(WINDOW, profile)
    assert result.passed is False
    assert result.check("pressure").passed is False


def test_evaluation_reports_each_named_check():
    result = evaluate_cure(WINDOW, _passing_profile())
    names = {c.name for c in result.checks}
    assert names == {"ramp_rate", "soak_duration", "overtemp", "pressure", "vacuum"}
