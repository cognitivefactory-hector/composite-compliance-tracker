"""Lot -> kit -> part genealogy (AC7118 §5.1.5 / §12 traceability)."""
from django.db import models

from tracker.cure.models import CureRun
from tracker.materials.models import MaterialLot


class Kit(models.Model):
    """A cut/layup kit built from one or more material lots."""

    kit_number = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(null=True, blank=True)
    lots = models.ManyToManyField(MaterialLot, related_name="kits")

    def __str__(self) -> str:
        return self.kit_number


class Part(models.Model):
    """A part laid up from a kit and (optionally) cured in a cure run."""

    part_number = models.CharField(max_length=100)
    serial = models.CharField(max_length=100)
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE, related_name="parts")
    cure_run = models.ForeignKey(
        CureRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="parts"
    )

    def __str__(self) -> str:
        return f"{self.part_number} / {self.serial}"
