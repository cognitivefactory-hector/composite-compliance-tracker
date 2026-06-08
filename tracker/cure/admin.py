from django.contrib import admin

from .models import CureRun, CureSpec


@admin.register(CureSpec)
class CureSpecAdmin(admin.ModelAdmin):
    list_display = ("name", "soak_temp_min", "soak_temp_max", "soak_min_duration")


@admin.register(CureRun)
class CureRunAdmin(admin.ModelAdmin):
    list_display = ("__str__", "spec", "started_at", "thermocouple_present")
    list_filter = ("spec", "facility")
