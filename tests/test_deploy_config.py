"""Guards the deploy config so the production domain can't silently 400."""
from django.conf import settings


def test_prod_host_allowed_by_default():
    # Baked into the default so a code deploy serves the custom domain without a
    # Render Blueprint env-var sync.
    assert "composite.hector-garza.com" in settings.ALLOWED_HOSTS


def test_prod_origin_is_csrf_trusted_by_default():
    assert "https://composite.hector-garza.com" in settings.CSRF_TRUSTED_ORIGINS
