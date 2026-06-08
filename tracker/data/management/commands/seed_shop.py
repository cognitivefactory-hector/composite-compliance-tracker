from django.core.management.base import BaseCommand

from tracker.data.seed import seed


class Command(BaseCommand):
    help = "Reset and load the synthetic composites shop (illustrative demo data)."

    def handle(self, *args, **options):
        summary = seed()
        self.stdout.write(self.style.SUCCESS("Synthetic shop seeded:"))
        for key, value in summary.items():
            self.stdout.write(f"  {key}: {value}")
