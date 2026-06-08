"""Deterministic cure-cycle window check (AC7118 §8.7.2 / §8.1).

Pure functions only — no Django, no I/O. A measured cure profile is evaluated
against a spec window (ramp rate, soak temperature/time, pressure, vacuum) and
gets a deterministic pass/fail per criterion. An LLM is never in this path.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class CureWindow:
    """The acceptable cure window from a cure spec."""

    soak_temp_min: float  # C
    soak_temp_max: float  # C — exceeding this is an overtemp excursion
    soak_min_duration: timedelta
    ramp_rate_min: float  # C/min during heat-up
    ramp_rate_max: float  # C/min during heat-up
    pressure_min: float
    pressure_max: float
    vacuum_min: float


@dataclass(frozen=True)
class ProfileSample:
    """One measured point of a cure run, elapsed since cure start."""

    elapsed: timedelta
    temperature: float
    pressure: float
    vacuum: float


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class CureEvaluation:
    passed: bool
    checks: tuple[CheckResult, ...]

    def check(self, name: str) -> CheckResult:
        for result in self.checks:
            if result.name == name:
                return result
        raise KeyError(name)


def _minutes(delta: timedelta) -> float:
    return delta.total_seconds() / 60.0


def _check_ramp_rate(window: CureWindow, samples: Sequence[ProfileSample]) -> CheckResult:
    """Each heat-up segment (rising toward the soak band) must stay within the
    allowed ramp-rate range."""
    for earlier, later in zip(samples, samples[1:], strict=False):
        if later.temperature <= earlier.temperature:
            continue  # not heating
        if earlier.temperature >= window.soak_temp_min:
            continue  # already at/above the soak band — not a ramp-up segment
        minutes = _minutes(later.elapsed - earlier.elapsed)
        if minutes <= 0:
            continue
        rate = (later.temperature - earlier.temperature) / minutes
        if rate > window.ramp_rate_max:
            return CheckResult("ramp_rate", False, f"ramp {rate:.2f} C/min exceeds max")
        if rate < window.ramp_rate_min:
            return CheckResult("ramp_rate", False, f"ramp {rate:.2f} C/min below min")
    return CheckResult("ramp_rate", True, "ramp within range")


def _check_soak_duration(window: CureWindow, samples: Sequence[ProfileSample]) -> CheckResult:
    """The longest contiguous in-band run must meet the minimum soak time."""
    longest = timedelta(0)
    run_start: timedelta | None = None
    for sample in samples:
        in_band = window.soak_temp_min <= sample.temperature <= window.soak_temp_max
        if in_band:
            if run_start is None:
                run_start = sample.elapsed
            longest = max(longest, sample.elapsed - run_start)
        else:
            run_start = None
    if longest >= window.soak_min_duration:
        return CheckResult("soak_duration", True, f"soak {_minutes(longest):.0f} min")
    return CheckResult(
        "soak_duration", False, f"soak {_minutes(longest):.0f} min below minimum"
    )


def _check_overtemp(window: CureWindow, samples: Sequence[ProfileSample]) -> CheckResult:
    for sample in samples:
        if sample.temperature > window.soak_temp_max:
            return CheckResult(
                "overtemp", False, f"{sample.temperature:.1f} C exceeds soak max"
            )
    return CheckResult("overtemp", True, "no overtemp excursion")


def _check_pressure(window: CureWindow, samples: Sequence[ProfileSample]) -> CheckResult:
    """Pressure must stay within the window throughout the in-band soak."""
    for sample in _soak_samples(window, samples):
        if not (window.pressure_min <= sample.pressure <= window.pressure_max):
            return CheckResult("pressure", False, f"{sample.pressure:.1f} out of window")
    return CheckResult("pressure", True, "pressure within window")


def _check_vacuum(window: CureWindow, samples: Sequence[ProfileSample]) -> CheckResult:
    """Vacuum must stay at or above the minimum throughout the in-band soak."""
    for sample in _soak_samples(window, samples):
        if sample.vacuum < window.vacuum_min:
            return CheckResult("vacuum", False, f"{sample.vacuum:.1f} below minimum")
    return CheckResult("vacuum", True, "vacuum maintained")


def _soak_samples(
    window: CureWindow, samples: Sequence[ProfileSample]
) -> list[ProfileSample]:
    return [
        s for s in samples if window.soak_temp_min <= s.temperature <= window.soak_temp_max
    ]


def evaluate_cure(
    window: CureWindow, samples: Sequence[ProfileSample]
) -> CureEvaluation:
    """Deterministic pass/fail of a measured profile against the cure window."""
    ordered = sorted(samples, key=lambda s: s.elapsed)
    checks = (
        _check_ramp_rate(window, ordered),
        _check_soak_duration(window, ordered),
        _check_overtemp(window, ordered),
        _check_pressure(window, ordered),
        _check_vacuum(window, ordered),
    )
    return CureEvaluation(passed=all(c.passed for c in checks), checks=checks)
