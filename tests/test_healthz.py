import pytest


def test_home_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Composite Compliance Tracker" in response.content
    # The synthetic-data / copyright disclaimer must be present on every page.
    assert b"synthetic data" in response.content


@pytest.mark.django_db
def test_healthz_reports_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
