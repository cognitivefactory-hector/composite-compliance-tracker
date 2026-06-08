"""Roll readiness up for the dashboard: per-criterion, per-section, overall.

Readiness is computed from records on every call (never stored as a tick).
"""
from dataclasses import dataclass, field
from datetime import datetime

from tracker.compliance.models import Criterion

from .engine import Readiness, ReadinessResult
from .evaluate import evaluate_criterion


@dataclass
class CriterionReadiness:
    criterion: Criterion
    result: ReadinessResult


@dataclass
class Rollup:
    """Counts for a group of criteria. Percent is over *applicable* criteria
    (NA excluded), because an NA is neither a pass nor a gap."""

    label: str
    items: list[CriterionReadiness] = field(default_factory=list)

    @property
    def compliant(self) -> int:
        return sum(i.result.status == Readiness.COMPLIANT for i in self.items)

    @property
    def gap(self) -> int:
        return sum(i.result.status == Readiness.GAP for i in self.items)

    @property
    def na(self) -> int:
        return sum(i.result.status == Readiness.NA for i in self.items)

    @property
    def applicable(self) -> int:
        return len(self.items) - self.na

    @property
    def percent(self) -> int:
        if self.applicable == 0:
            return 100
        return round(self.compliant / self.applicable * 100)


def evaluate_all(as_of: datetime) -> list[CriterionReadiness]:
    return [
        CriterionReadiness(c, evaluate_criterion(c, as_of))
        for c in Criterion.objects.all()
    ]


def section_rollups(items: list[CriterionReadiness]) -> list[Rollup]:
    by_section: dict[str, Rollup] = {}
    for item in items:
        section = item.criterion.section
        by_section.setdefault(section, Rollup(label=section)).items.append(item)
    return [by_section[key] for key in sorted(by_section)]


def overall_rollup(items: list[CriterionReadiness]) -> Rollup:
    return Rollup(label="overall", items=list(items))
