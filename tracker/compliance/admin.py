from django.contrib import admin

from .models import NCR, Criterion, CriterionStatus, EvidenceLink


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ("criterion_id", "title", "section", "scope", "evidence_type")
    list_filter = ("section", "scope", "evidence_type")
    search_fields = ("criterion_id", "title")


@admin.register(CriterionStatus)
class CriterionStatusAdmin(admin.ModelAdmin):
    list_display = ("criterion", "is_na", "attested", "procedure_reference")
    list_filter = ("is_na", "attested")


@admin.register(EvidenceLink)
class EvidenceLinkAdmin(admin.ModelAdmin):
    list_display = ("criterion", "content_type", "object_id", "note")


@admin.register(NCR)
class NCRAdmin(admin.ModelAdmin):
    list_display = ("__str__", "criterion", "opened_at", "is_closed")
    list_filter = ("is_closed",)
