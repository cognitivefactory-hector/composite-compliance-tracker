"""AC7118 criteria, manual status/attestation, evidence links, and NCRs.

Criteria define *what* must be shown and *how* it is evidenced; readiness is
computed (see tracker/readiness/) rather than stored as a tick. This module
holds only the manual inputs a human still owns: NA explanations, documentation
attestations, explicit evidence links, and nonconformance records.
"""
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


class Criterion(models.Model):
    """A (paraphrased) AC7118 criterion. NOT the verbatim © PRI text."""

    class EvidenceType(models.TextChoices):
        OUT_TIME = "out_time", "Out-time / shelf-life records"
        CURE = "cure", "Cure-cycle records"
        DOCUMENTATION = "documentation", "Documentation (manual attestation)"

    criterion_id = models.CharField(max_length=20, unique=True)  # e.g. "5.1.12"
    title = models.CharField(max_length=300)  # paraphrased / representative
    section = models.CharField(max_length=20)  # e.g. "5.1"
    scope = models.CharField(max_length=20, default="PAR")
    evidence_type = models.CharField(max_length=20, choices=EvidenceType.choices)

    class Meta:
        ordering = ["criterion_id"]

    def __str__(self) -> str:
        return f"{self.criterion_id} — {self.title}"


class CriterionStatus(models.Model):
    """The manual inputs for a criterion: NA explanation and/or a documentation
    attestation. Data-backed readiness is computed elsewhere and not stored here.
    """

    criterion = models.OneToOneField(
        Criterion, on_delete=models.CASCADE, related_name="status"
    )
    is_na = models.BooleanField(default=False)
    na_explanation = models.TextField(blank=True)
    # For documentation-only criteria: the procedure reference + human sign-off.
    procedure_reference = models.CharField(max_length=200, blank=True)
    attested = models.BooleanField(default=False)
    signed_by = models.CharField(max_length=200, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Status for {self.criterion.criterion_id}"

    def clean(self) -> None:
        # An NA is only valid with an explanation (AC7118 expects justified NAs).
        if self.is_na and not self.na_explanation.strip():
            raise ValidationError({"na_explanation": "An NA requires an explanation."})


class EvidenceLink(models.Model):
    """An explicit link from a criterion to a concrete record (any model),
    powering 'click a ready status → land on the proof'."""

    criterion = models.ForeignKey(
        Criterion, on_delete=models.CASCADE, related_name="evidence_links"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    record = GenericForeignKey("content_type", "object_id")
    note = models.CharField(max_length=300, blank=True)

    def __str__(self) -> str:
        return f"{self.criterion.criterion_id} ← {self.record}"


class NCR(models.Model):
    """A nonconformance record opened for a negative finding. No auto-closure —
    a qualified person dispositions and closes it."""

    criterion = models.ForeignKey(
        Criterion, on_delete=models.CASCADE, related_name="ncrs"
    )
    description = models.TextField()
    opened_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)
    disposition = models.TextField(blank=True)

    class Meta:
        verbose_name = "NCR"
        verbose_name_plural = "NCRs"
        ordering = ["-opened_at"]

    def __str__(self) -> str:
        state = "closed" if self.is_closed else "open"
        return f"NCR {self.pk} ({state}) — {self.criterion.criterion_id}"

    @classmethod
    def open_for(cls, criterion: Criterion, description: str) -> "NCR":
        return cls.objects.create(criterion=criterion, description=description)
