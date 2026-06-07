from django.contrib import admin

from .models import ColdStorageEvent, Material, MaterialLot


class ColdStorageEventInline(admin.TabularInline):
    model = ColdStorageEvent
    extra = 0


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "default_out_time_limit", "pot_life")
    list_filter = ("kind",)


@admin.register(MaterialLot)
class MaterialLotAdmin(admin.ModelAdmin):
    list_display = ("lot_number", "material", "manufactured_at", "expiration")
    search_fields = ("lot_number", "material__name")
    inlines = [ColdStorageEventInline]


@admin.register(ColdStorageEvent)
class ColdStorageEventAdmin(admin.ModelAdmin):
    list_display = ("lot", "event_type", "occurred_at")
    list_filter = ("event_type",)
