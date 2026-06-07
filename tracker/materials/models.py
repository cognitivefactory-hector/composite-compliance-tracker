"""Material lots and cold-storage events.

Models store the facts (lots, spec limits, freeze/thaw events); all
time-sensitive math is delegated to the deterministic, pure-Python engine in
``outtime.py`` — the models never reimplement a limit calculation.
"""
from datetime import datetime, timedelta

from django.db import models

from . import outtime


class Material(models.Model):
    """A prepreg/adhesive/resin with its built-in spec limits."""

    class Kind(models.TextChoices):
        PREPREG = "prepreg", "Prepreg"
        ADHESIVE = "adhesive", "Adhesive"
        RESIN = "resin", "Resin"

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    # The material's default (spec) accumulated out-time limit. An individual
    # lot may carry an engineering override that takes precedence.
    default_out_time_limit = models.DurationField()
    # Working life of mixed resin/adhesive; null for materials that aren't mixed.
    pot_life = models.DurationField(null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class MaterialLot(models.Model):
    """A specific lot of a material, with its shelf life and any override."""

    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="lots"
    )
    lot_number = models.CharField(max_length=100)
    manufactured_at = models.DateTimeField()
    # Calendar shelf-life expiration (from manufacture or recertification).
    expiration = models.DateTimeField()
    # "Engineering takes precedence": when set, overrides the material default.
    out_time_limit_override = models.DurationField(null=True, blank=True)
    # When mixed resin/adhesive's pot life started; null until mixed.
    mixed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.material.name} — lot {self.lot_number}"

    def _events(self) -> list[outtime.StorageEvent]:
        return [
            outtime.StorageEvent(outtime.EventType(e.event_type), e.occurred_at)
            for e in self.storage_events.all()
        ]

    def resolved_out_time_limit(self) -> outtime.ResolvedLimit:
        return outtime.resolve_out_time_limit(
            default=self.material.default_out_time_limit,
            override=self.out_time_limit_override,
        )

    def accumulated_out_time(self, as_of: datetime) -> timedelta:
        return outtime.accumulated_out_time(self._events(), as_of=as_of)

    def out_time_status(self, as_of: datetime) -> outtime.OutTimeStatus:
        return outtime.out_time_status(
            accumulated=self.accumulated_out_time(as_of),
            limit=self.resolved_out_time_limit().value,
        )

    def shelf_life_expired(self, as_of: datetime) -> bool:
        return outtime.shelf_life_expired(expiration=self.expiration, as_of=as_of)

    def pot_life_remaining(self, as_of: datetime) -> timedelta | None:
        if self.mixed_at is None or self.material.pot_life is None:
            return None
        return outtime.pot_life_remaining(
            mixed_at=self.mixed_at, pot_life=self.material.pot_life, as_of=as_of
        )


class ColdStorageEvent(models.Model):
    """A removal-from / return-to cold storage transition for a lot."""

    lot = models.ForeignKey(
        MaterialLot, on_delete=models.CASCADE, related_name="storage_events"
    )
    event_type = models.CharField(
        max_length=20, choices=[(e.value, e.name.title()) for e in outtime.EventType]
    )
    occurred_at = models.DateTimeField()

    class Meta:
        ordering = ["occurred_at"]

    def __str__(self) -> str:
        return f"{self.lot} — {self.event_type} @ {self.occurred_at:%Y-%m-%d %H:%M}"
