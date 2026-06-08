"""Lot -> kit -> part genealogy."""
from datetime import UTC, datetime, timedelta

import pytest

from tracker.materials.models import Material, MaterialLot
from tracker.trace.models import Kit, Part

pytestmark = pytest.mark.django_db


def _lot(lot_number: str) -> MaterialLot:
    material = Material.objects.create(
        name="Hexcel 8552", kind="prepreg", default_out_time_limit=timedelta(days=30)
    )
    return MaterialLot.objects.create(
        material=material,
        lot_number=lot_number,
        manufactured_at=datetime(2026, 1, 1, tzinfo=UTC),
        expiration=datetime(2026, 12, 1, tzinfo=UTC),
    )


def test_part_traces_back_to_its_lots_through_a_kit():
    lot_a = _lot("LOT-A")
    lot_b = _lot("LOT-B")
    kit = Kit.objects.create(kit_number="KIT-1")
    kit.lots.add(lot_a, lot_b)
    part = Part.objects.create(part_number="PN-1", serial="SN-1", kit=kit)

    assert set(part.kit.lots.all()) == {lot_a, lot_b}
    assert part in kit.parts.all()


def test_lot_knows_which_kits_consume_it():
    lot = _lot("LOT-A")
    kit = Kit.objects.create(kit_number="KIT-1")
    kit.lots.add(lot)
    assert kit in lot.kits.all()
