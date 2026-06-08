"""Tests for the optional, gated Claude assist. The API is always mocked —
no network, no key required in CI. Proves the assist is advisory: gated on the
key, and incapable of changing a computed status or persisting anything.
"""
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.utils import timezone

from tracker.assist import client as assist
from tracker.compliance.models import NCR, Criterion
from tracker.readiness.engine import Readiness
from tracker.readiness.evaluate import evaluate_criterion


def test_assist_disabled_without_key():
    with override_settings(ANTHROPIC_API_KEY=""):
        assert assist.is_enabled() is False


def test_assist_enabled_with_key():
    with override_settings(ANTHROPIC_API_KEY="sk-test"):
        assert assist.is_enabled() is True


def test_draft_without_key_raises():
    with override_settings(ANTHROPIC_API_KEY=""):
        with pytest.raises(assist.AssistDisabledError):
            assist.draft_ncr_explanation("5.1.12", "Out-time tracked", "lot expired")


@override_settings(ANTHROPIC_API_KEY="sk-test")
@patch("tracker.assist.client._complete", return_value="Drafted NCR text.")
def test_draft_ncr_returns_text(mock_complete):
    text = assist.draft_ncr_explanation("5.1.12", "Out-time tracked", "lot expired")
    assert text == "Drafted NCR text."
    # The criterion context must reach the prompt.
    system, user = mock_complete.call_args.args[0], mock_complete.call_args.args[1]
    assert "5.1.12" in user
    assert "advisory" in system.lower()


@override_settings(ANTHROPIC_API_KEY="sk-test")
def test_import_criteria_returns_structured_rows():
    fake = assist.CriteriaImport(
        criteria=[assist.CriterionDraft(criterion_id="5.1.12", title="Out-time", section="5.1")]
    )
    with patch("tracker.assist.client._parse", return_value=fake):
        rows = assist.import_criteria("...licensed export...")
    assert rows == [{"criterion_id": "5.1.12", "title": "Out-time", "section": "5.1"}]


@pytest.mark.django_db
@override_settings(ANTHROPIC_API_KEY="sk-test")
@patch("tracker.assist.client._complete", return_value="Drafted text.")
def test_drafting_is_advisory_changes_no_state(mock_complete):
    # An out-time criterion with no lots computes GAP. Drafting must not change
    # that, and must not create any NCR.
    criterion = Criterion.objects.create(
        criterion_id="5.1.12",
        title="Out-time tracked to spec limits",
        section="5.1",
        scope="PAR",
        evidence_type=Criterion.EvidenceType.OUT_TIME,
    )

    before = evaluate_criterion(criterion, as_of=timezone.now()).status
    assist.draft_ncr_explanation(criterion.criterion_id, criterion.title, "no lots")
    after = evaluate_criterion(criterion, as_of=timezone.now()).status
    assert before == after == Readiness.GAP
    assert NCR.objects.count() == 0


@pytest.mark.django_db
def test_draft_ncr_view_404_when_disabled(client):
    with override_settings(ANTHROPIC_API_KEY=""):
        response = client.post("/criteria/5.1.12/draft-ncr/")
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(ANTHROPIC_API_KEY="sk-test")
@patch("tracker.assist.client._complete", return_value="Drafted NCR explanation.")
def test_draft_ncr_view_returns_draft_when_enabled(mock_complete, client):
    Criterion.objects.create(
        criterion_id="5.1.12",
        title="Out-time tracked",
        section="5.1",
        scope="PAR",
        evidence_type=Criterion.EvidenceType.OUT_TIME,
    )
    response = client.post("/criteria/5.1.12/draft-ncr/")
    assert response.status_code == 200
    assert b"Drafted NCR explanation." in response.content
