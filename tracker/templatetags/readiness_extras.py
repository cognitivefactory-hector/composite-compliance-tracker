"""Small presentation helpers for the readiness templates."""
from datetime import timedelta

from django import template

register = template.Library()


@register.filter
def pct(value: float) -> int:
    """Fraction (0.92) -> whole percent (92)."""
    try:
        return round(float(value) * 100)
    except (TypeError, ValueError):
        return 0


@register.filter
def clamp100(value: float) -> float:
    """Clamp an already-percent number into [0, 100] for a bar width."""
    try:
        return min(100.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


@register.filter
def as_days(value: timedelta) -> str:
    """Render a timedelta as a signed day count with one decimal."""
    if not isinstance(value, timedelta):
        return ""
    return f"{value.total_seconds() / 86400:.1f} d"
