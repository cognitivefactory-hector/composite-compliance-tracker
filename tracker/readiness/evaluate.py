"""Database-backed readiness evaluation.

Builds evidence facts from real records and delegates the decision to the pure
engine. A criterion is never auto-green: if an active lot's record is missing,
expired, or out of limit, the criterion computes as a GAP.
"""
from datetime import datetime

from tracker.compliance.models import Criterion
from tracker.cure.models import CureRun
from tracker.materials.models import MaterialLot
from tracker.materials.outtime import AlertLevel

from . import engine


def _lot_evidence(as_of: datetime) -> list[engine.LotEvidence]:
    evidence = []
    for lot in MaterialLot.objects.filter(is_active=True):
        evidence.append(
            engine.LotEvidence(
                lot_id=lot.pk,
                has_out_time_record=lot.storage_events.exists(),
                breached=lot.out_time_status(as_of).level == AlertLevel.BREACH,
                shelf_expired=lot.shelf_life_expired(as_of),
            )
        )
    return evidence


def _cure_evidence() -> list[engine.CureEvidence]:
    return [
        engine.CureEvidence(
            run_id=run.pk,
            complete=not run.missing_required_fields(),
            passed=run.evaluate().passed,
        )
        for run in CureRun.objects.all()
    ]


def evaluate_criterion(
    criterion: Criterion, as_of: datetime
) -> engine.ReadinessResult:
    """Compute a criterion's readiness from current records.

    A justified NA short-circuits; otherwise the evidence type selects which
    records back the criterion.
    """
    status = getattr(criterion, "status", None)
    if status is not None and status.is_na:
        return engine.na_readiness(status.na_explanation)

    if criterion.evidence_type == Criterion.EvidenceType.OUT_TIME:
        return engine.out_time_readiness(_lot_evidence(as_of))
    if criterion.evidence_type == Criterion.EvidenceType.CURE:
        return engine.cure_readiness(_cure_evidence())
    if criterion.evidence_type == Criterion.EvidenceType.DOCUMENTATION:
        if status is None:
            return engine.documentation_readiness("", attested=False)
        return engine.documentation_readiness(
            status.procedure_reference, attested=status.attested
        )
    return engine.ReadinessResult(
        engine.Readiness.GAP, f"unknown evidence type: {criterion.evidence_type}"
    )
