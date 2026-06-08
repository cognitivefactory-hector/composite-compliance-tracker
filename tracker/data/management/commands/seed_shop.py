from django.core.management.base import BaseCommand

from tracker.compliance.models import Criterion
from tracker.data.seed import seed


class Command(BaseCommand):
    help = "Reset and load the synthetic composites shop (illustrative demo data)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Only seed when no criteria exist; skip if already populated. "
            "Use on a persistent DB so restarts don't wipe and reseed.",
        )

    def handle(self, *args, **options):
        if options["if_empty"] and Criterion.objects.exists():
            self.stdout.write("Shop already seeded — skipping (--if-empty).")
            return
        summary = seed()
        self.stdout.write(self.style.SUCCESS("Synthetic shop seeded:"))
        for key, value in summary.items():
            self.stdout.write(f"  {key}: {value}")
