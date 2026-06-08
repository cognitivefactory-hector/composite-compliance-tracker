from django.contrib import admin

from .models import Kit, Part


@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ("kit_number", "created_at")
    filter_horizontal = ("lots",)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ("part_number", "serial", "kit", "cure_run")
