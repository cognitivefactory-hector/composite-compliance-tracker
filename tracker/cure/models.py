"""Cure specs and cure runs (AC7118 §8.7.2 / §8.1).

The model stores the spec window and the §8.7.2 record fields plus the measured
profile; the deterministic pass/fail is delegated to the pure engine in
``window.py``.
"""
from datetime import timedelta

from django.db import models

from . import window

# AC7118 §8.7.2 fields that must be present for a cure record to be complete.
REQUIRED_RECORD_FIELDS = ("facility", "equipment_id", "started_at", "part_serials")


class CureSpec(models.Model):
    """The acceptable cure window for a process/material."""

    name = models.CharField(max_length=200)
    soak_temp_min = models.FloatField()
    soak_temp_max = models.FloatField()
    soak_min_duration = models.DurationField()
    ramp_rate_min = models.FloatField()
    ramp_rate_max = models.FloatField()
    pressure_min = models.FloatField()
    pressure_max = models.FloatField()
    vacuum_min = models.FloatField()

    def __str__(self) -> str:
        return self.name

    def window(self) -> window.CureWindow:
        return window.CureWindow(
            soak_temp_min=self.soak_temp_min,
            soak_temp_max=self.soak_temp_max,
            soak_min_duration=self.soak_min_duration,
            ramp_rate_min=self.ramp_rate_min,
            ramp_rate_max=self.ramp_rate_max,
            pressure_min=self.pressure_min,
            pressure_max=self.pressure_max,
            vacuum_min=self.vacuum_min,
        )


class CureRun(models.Model):
    """A logged cure cycle and its measured profile.

    ``profile`` is a list of ``{minute, temperature, pressure, vacuum}`` points;
    storing the time series as JSON keeps the whole curve together for both the
    deterministic check and the M5 Plotly chart.
    """

    spec = models.ForeignKey(CureSpec, on_delete=models.PROTECT, related_name="runs")
    facility = models.CharField(max_length=200, blank=True)
    equipment_id = models.CharField(max_length=100, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    part_serials = models.JSONField(default=list, blank=True)
    thermocouple_present = models.BooleanField(default=False)
    process_panel_present = models.BooleanField(default=False)
    profile = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return f"Cure {self.pk} — {self.spec.name} @ {self.facility}"

    def samples(self) -> list[window.ProfileSample]:
        return [
            window.ProfileSample(
                elapsed=timedelta(minutes=point["minute"]),
                temperature=point["temperature"],
                pressure=point["pressure"],
                vacuum=point["vacuum"],
            )
            for point in self.profile
        ]

    def evaluate(self) -> window.CureEvaluation:
        return window.evaluate_cure(self.spec.window(), self.samples())

    def missing_required_fields(self) -> list[str]:
        """Names of AC7118 §8.7.2 record fields that are empty."""
        missing = []
        for field in REQUIRED_RECORD_FIELDS:
            value = getattr(self, field)
            if value in (None, "", [], {}):
                missing.append(field)
        return missing
