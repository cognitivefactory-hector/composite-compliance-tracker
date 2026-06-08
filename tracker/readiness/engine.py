"""Pure readiness-from-evidence decision logic — the project's thesis.

A criterion is COMPLIANT only when its linked evidence exists and is valid; it is
never auto-green. These functions take already-evaluated facts (not the database)
so the decision is deterministic and testable without I/O; the DB-querying
wrappers live in ``evaluate.py``.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum


class Readiness(StrEnum):
    COMPLIANT = "compliant"  # ready — evidence exists and is valid
    GAP = "gap"  # not ready
    NA = "na"  # not applicable (with explanation)


@dataclass(frozen=True)
class ReadinessResult:
    status: Readiness
    reason: str
    # Pointers to the records behind the decision — powers "click a status →
    # land on the proof". For a GAP these are the offending records.
    evidence_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class LotEvidence:
    lot_id: int
    has_out_time_record: bool
    breached: bool
    shelf_expired: bool

    @property
    def is_problem(self) -> bool:
        return (not self.has_out_time_record) or self.breached or self.shelf_expired


def out_time_readiness(lots: Sequence[LotEvidence]) -> ReadinessResult:
    """COMPLIANT only if there is at least one active lot and every active lot
    has a current, in-limit out-time record."""
    if not lots:
        return ReadinessResult(Readiness.GAP, "no active lots provide evidence")
    problems = [lot for lot in lots if lot.is_problem]
    if problems:
        return ReadinessResult(
            Readiness.GAP,
            f"{len(problems)} lot(s) missing, expired, or out of limit",
            tuple(lot.lot_id for lot in problems),
        )
    return ReadinessResult(
        Readiness.COMPLIANT,
        f"all {len(lots)} active lot(s) in limit",
        tuple(lot.lot_id for lot in lots),
    )


@dataclass(frozen=True)
class CureEvidence:
    run_id: int
    complete: bool  # all AC7118 §8.7.2 required fields present
    passed: bool  # measured profile inside the cure window

    @property
    def is_problem(self) -> bool:
        return not (self.complete and self.passed)


def cure_readiness(runs: Sequence[CureEvidence]) -> ReadinessResult:
    """COMPLIANT only if at least one cure run exists and every run is a
    complete record that passed its window."""
    if not runs:
        return ReadinessResult(Readiness.GAP, "no cure records provide evidence")
    problems = [run for run in runs if run.is_problem]
    if problems:
        return ReadinessResult(
            Readiness.GAP,
            f"{len(problems)} cure run(s) incomplete or out of window",
            tuple(run.run_id for run in problems),
        )
    return ReadinessResult(
        Readiness.COMPLIANT,
        f"all {len(runs)} cure run(s) complete and in window",
        tuple(run.run_id for run in runs),
    )


def documentation_readiness(
    procedure_reference: str, attested: bool
) -> ReadinessResult:
    """A documentation-only criterion is COMPLIANT only with an attached
    procedure reference AND a human attestation — never a bare tick."""
    if not procedure_reference:
        return ReadinessResult(Readiness.GAP, "no procedure reference attached")
    if not attested:
        return ReadinessResult(Readiness.GAP, "awaiting human attestation")
    return ReadinessResult(Readiness.COMPLIANT, f"attested against {procedure_reference}")


def na_readiness(explanation: str) -> ReadinessResult:
    """Not-applicable is only valid with an explanation."""
    if not explanation:
        return ReadinessResult(Readiness.GAP, "NA requires an explanation")
    return ReadinessResult(Readiness.NA, explanation)
