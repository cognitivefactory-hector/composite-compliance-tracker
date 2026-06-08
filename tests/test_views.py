"""View/template tests for the M5 UI, driven by the synthetic seed.

The seed is loaded at the real clock so the near-breach lot's live out-time
aligns with the views' timezone.now().
"""
import pytest
from django.utils import timezone

from tracker.cure.models import CureRun
from tracker.data.seed import seed
from tracker.materials.models import MaterialLot

pytestmark = pytest.mark.django_db


@pytest.fixture
def shop():
    seed(now=timezone.now())


def test_dashboard_renders_with_seeded_readiness(client, shop):
    response = client.get("/")
    assert response.status_code == 200
    body = response.content
    assert b"Audit readiness" in body
    assert b"synthetic data" in body  # disclaimer present on every page


def test_dashboard_shows_a_firing_out_time_alert(client, shop):
    # The near-breach lot (~92%) must surface as a critical alert on screen.
    body = client.get("/").content.decode()
    assert "critical" in body


def test_out_time_criterion_page_is_a_gap_and_lists_the_expired_lot(client, shop):
    response = client.get("/criteria/5.1.12/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "gap" in body
    assert "HX-0900" in body  # the expired lot
    assert "blocks readiness" in body


def test_attested_documentation_criterion_shows_compliant(client, shop):
    body = client.get("/criteria/4.3.1/").content.decode()
    assert "compliant" in body
    assert "QOP-4.3.1" in body  # the procedure reference


def test_lot_detail_shows_gauge_for_near_breach_lot(client, shop):
    lot = MaterialLot.objects.get(lot_number="HX-1002")
    body = client.get(f"/lots/{lot.pk}/").content.decode()
    assert "critical" in body
    assert "of limit" in body


def test_cure_detail_renders_plotly_chart_and_pass_fail(client, shop):
    run = CureRun.objects.first()
    body = client.get(f"/cure/{run.pk}/").content.decode()
    assert "plotly" in body.lower()  # the embedded chart
    assert "pass" in body
    assert "ramp_rate" in body  # per-check breakdown


def test_traceability_page_shows_genealogy(client, shop):
    body = client.get("/trace/").content.decode()
    assert "KIT-3007" in body
    assert "HX-1001" in body  # a lot in the kit


def test_healthz_still_ok(client):
    assert client.get("/healthz").json() == {"status": "ok", "database": "ok"}
