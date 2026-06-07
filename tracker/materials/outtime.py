"""Deterministic out-time / shelf-life / pot-life engine (AC7118 §5.1.12).

Pure functions only — no Django, no I/O, no clock. Every time-dependent
calculation takes an explicit ``as_of`` so results are reproducible and an LLM
is never in the path of a safety-relevant limit. Django models (see
``models.py``) wrap these functions; tests exercise them directly.
"""
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class EventType(StrEnum):
    """A cold-storage transition for a material lot."""

    REMOVED = "removed"  # taken out of cold storage — out-time starts accruing
    RETURNED = "returned"  # returned to cold storage — out-time stops accruing


@dataclass(frozen=True)
class StorageEvent:
    event_type: EventType
    occurred_at: datetime


def accumulated_out_time(
    events: Iterable[StorageEvent], as_of: datetime
) -> timedelta:
    """Total time a lot has spent OUT of cold storage, across every cycle.

    The lot is assumed to start in cold storage. A ``REMOVED`` opens an
    out-interval; the next ``RETURNED`` closes it. Time spent in cold storage
    never accrues. An interval still open at ``as_of`` accrues up to ``as_of``
    (a live clock), so a lot left out keeps accumulating until it is returned.
    """
    total = timedelta(0)
    out_since: datetime | None = None
    for event in sorted(events, key=lambda e: e.occurred_at):
        if event.event_type == EventType.REMOVED:
            if out_since is None:
                out_since = event.occurred_at
        else:  # RETURNED
            if out_since is not None:
                total += event.occurred_at - out_since
                out_since = None
    if out_since is not None:
        total += as_of - out_since
    return total


class LimitSource(StrEnum):
    """Which value governed a limit — recorded for the audit trail."""

    DEFAULT = "default"  # the material's built-in spec limit
    ENGINEERING = "engineering"  # a customer/engineering override took precedence


@dataclass(frozen=True)
class ResolvedLimit:
    value: timedelta
    source: LimitSource


def resolve_out_time_limit(
    default: timedelta, override: timedelta | None = None
) -> ResolvedLimit:
    """Engineering/customer spec takes precedence over the material default."""
    if override is not None:
        return ResolvedLimit(value=override, source=LimitSource.ENGINEERING)
    return ResolvedLimit(value=default, source=LimitSource.DEFAULT)


class AlertLevel(StrEnum):
    OK = "ok"
    WARNING = "warning"  # approaching the limit (default >= 80%)
    CRITICAL = "critical"  # close to the limit (default >= 90%)
    BREACH = "breach"  # at or past the limit (>= 100%)


@dataclass(frozen=True)
class OutTimeStatus:
    accumulated: timedelta
    limit: timedelta
    fraction: float
    level: AlertLevel
    remaining: timedelta  # negative once breached


def out_time_status(
    accumulated: timedelta,
    limit: timedelta,
    thresholds: tuple[float, float] = (0.8, 0.9),
) -> OutTimeStatus:
    """Classify accumulated out-time against its limit.

    ``thresholds`` are the (warning, critical) fractions; breach is always at
    or beyond 100%. Alerts are proactive: WARNING/CRITICAL fire *before* the
    limit is reached so a lot can be returned before an excursion occurs.
    """
    warning, critical = thresholds
    fraction = accumulated / limit
    if fraction >= 1.0:
        level = AlertLevel.BREACH
    elif fraction >= critical:
        level = AlertLevel.CRITICAL
    elif fraction >= warning:
        level = AlertLevel.WARNING
    else:
        level = AlertLevel.OK
    return OutTimeStatus(
        accumulated=accumulated,
        limit=limit,
        fraction=fraction,
        level=level,
        remaining=limit - accumulated,
    )


def shelf_life_expired(expiration: datetime, as_of: datetime) -> bool:
    """Shelf life is calendar-based (from manufacture or recertification).

    Expired at or after the expiration instant — the material is no longer
    usable the moment it expires.
    """
    return as_of >= expiration


def pot_life_remaining(
    mixed_at: datetime, pot_life: timedelta, as_of: datetime
) -> timedelta:
    """Time left in a mixed resin/adhesive's working life. Starts at mix.

    Negative once the pot life is exceeded.
    """
    return (mixed_at + pot_life) - as_of


def thawed_before_open(thaw_completed: datetime | None, opened: datetime) -> bool:
    """AC7118 §5.1.15: a frozen package must be fully thawed before it is opened
    (else condensation contaminates the prepreg). Valid only if a thaw completed
    at or before the package was opened.
    """
    if thaw_completed is None:
        return False
    return thaw_completed <= opened


def resealed_before_return(resealed: datetime | None, returned: datetime) -> bool:
    """AC7118 §5.1.13: a package must be resealed before being returned to cold
    storage. Valid only if a reseal occurred at or before the return.
    """
    if resealed is None:
        return False
    return resealed <= returned
