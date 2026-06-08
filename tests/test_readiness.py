"""Crown-jewel tests for the pure readiness-from-evidence engine.

The thesis: a criterion is COMPLIANT only when its evidence exists and is valid.
No database here — see tracker/readiness/engine.py.
"""
from tracker.readiness.engine import (
    CureEvidence,
    LotEvidence,
    Readiness,
    cure_readiness,
    documentation_readiness,
    na_readiness,
    out_time_readiness,
)


def _good_lot(lot_id: int) -> LotEvidence:
    return LotEvidence(
        lot_id=lot_id, has_out_time_record=True, breached=False, shelf_expired=False
    )


# --- Out-time-backed criterion (e.g. AC7118 §5.1.12) ---

def test_out_time_with_no_lots_is_a_gap_not_auto_green():
    result = out_time_readiness([])
    assert result.status == Readiness.GAP


def test_out_time_all_lots_valid_is_compliant():
    result = out_time_readiness([_good_lot(1), _good_lot(2)])
    assert result.status == Readiness.COMPLIANT
    assert set(result.evidence_ids) == {1, 2}


def test_out_time_breached_lot_is_a_gap():
    breached = LotEvidence(lot_id=7, has_out_time_record=True, breached=True, shelf_expired=False)
    result = out_time_readiness([_good_lot(1), breached])
    assert result.status == Readiness.GAP
    assert 7 in result.evidence_ids


def test_out_time_shelf_expired_lot_is_a_gap():
    expired = LotEvidence(lot_id=8, has_out_time_record=True, breached=False, shelf_expired=True)
    result = out_time_readiness([expired])
    assert result.status == Readiness.GAP
    assert 8 in result.evidence_ids


def test_out_time_missing_record_is_a_gap_the_thesis():
    # A lot that should be tracked but has no out-time record → NOT ready,
    # even though a human eyeballing a binder might tick "yes, we track that".
    missing = LotEvidence(lot_id=9, has_out_time_record=False, breached=False, shelf_expired=False)
    result = out_time_readiness([missing])
    assert result.status == Readiness.GAP
    assert 9 in result.evidence_ids


# --- Cure-backed criterion (e.g. AC7118 §8.7.2) ---

def test_cure_with_no_runs_is_a_gap():
    assert cure_readiness([]).status == Readiness.GAP


def test_cure_incomplete_run_is_a_gap():
    runs = [CureEvidence(run_id=1, complete=False, passed=True)]
    result = cure_readiness(runs)
    assert result.status == Readiness.GAP
    assert 1 in result.evidence_ids


def test_cure_failed_run_is_a_gap():
    runs = [CureEvidence(run_id=2, complete=True, passed=False)]
    result = cure_readiness(runs)
    assert result.status == Readiness.GAP
    assert 2 in result.evidence_ids


def test_cure_all_complete_and_passing_is_compliant():
    runs = [CureEvidence(run_id=1, complete=True, passed=True)]
    assert cure_readiness(runs).status == Readiness.COMPLIANT


# --- Documentation-only criterion: manual attestation + procedure ref ---

def test_documentation_without_procedure_reference_is_a_gap():
    assert documentation_readiness(procedure_reference="", attested=True).status == Readiness.GAP


def test_documentation_with_reference_but_not_attested_is_a_gap():
    result = documentation_readiness(procedure_reference="QOP-12", attested=False)
    assert result.status == Readiness.GAP


def test_documentation_attested_with_reference_is_compliant():
    result = documentation_readiness(procedure_reference="QOP-12", attested=True)
    assert result.status == Readiness.COMPLIANT


# --- NA requires an explanation ---

def test_na_without_explanation_is_not_valid_na():
    assert na_readiness(explanation="").status == Readiness.GAP


def test_na_with_explanation_is_na():
    assert na_readiness(explanation="No liquid resin used on this path").status == Readiness.NA
