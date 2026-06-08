from django.db import connection
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from tracker.assist import client as assist
from tracker.compliance.models import NCR, Criterion
from tracker.cure.charts import cure_profile_html
from tracker.cure.models import CureRun
from tracker.materials.models import MaterialLot
from tracker.readiness import report
from tracker.readiness.engine import Readiness
from tracker.readiness.evaluate import evaluate_criterion
from tracker.trace.models import Kit


def healthz(request):
    """Liveness/readiness probe: confirms the process is up and the DB answers."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:  # pragma: no cover - exercised only on DB outage
        return JsonResponse({"status": "error", "database": str(exc)}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


def dashboard(request):
    now = timezone.now()
    items = report.evaluate_all(now)
    sections = report.section_rollups(items)
    overall = report.overall_rollup(items)
    lots = [
        {"lot": lot, "status": lot.out_time_status(now), "expired": lot.shelf_life_expired(now)}
        for lot in MaterialLot.objects.filter(is_active=True).select_related("material")
    ]
    return render(
        request,
        "tracker/dashboard.html",
        {
            "now": now,
            "overall": overall,
            "sections": sections,
            "gaps": [i for i in items if i.result.status == Readiness.GAP],
            "open_ncrs": NCR.objects.filter(is_closed=False).select_related("criterion"),
            "lots": lots,
            "cure_runs": CureRun.objects.select_related("spec").all(),
        },
    )


def criterion_detail(request, criterion_id):
    now = timezone.now()
    criterion = get_object_or_404(Criterion, criterion_id=criterion_id)
    result = evaluate_criterion(criterion, as_of=now)
    problem_ids = set(result.evidence_ids)

    context = {
        "criterion": criterion,
        "result": result,
        "now": now,
        "assist_enabled": assist.is_enabled(),
    }
    if criterion.evidence_type == Criterion.EvidenceType.OUT_TIME:
        context["lot_evidence"] = [
            {
                "lot": lot,
                "status": lot.out_time_status(now),
                "expired": lot.shelf_life_expired(now),
                "is_problem": lot.pk in problem_ids,
            }
            for lot in MaterialLot.objects.filter(is_active=True).select_related("material")
        ]
    elif criterion.evidence_type == Criterion.EvidenceType.CURE:
        context["cure_evidence"] = [
            {"run": run, "evaluation": run.evaluate(), "missing": run.missing_required_fields()}
            for run in CureRun.objects.select_related("spec").all()
        ]
    else:
        context["status_record"] = getattr(criterion, "status", None)
    return render(request, "tracker/criterion_detail.html", context)


def lot_detail(request, pk):
    now = timezone.now()
    lot = get_object_or_404(MaterialLot.objects.select_related("material"), pk=pk)
    return render(
        request,
        "tracker/lot_detail.html",
        {
            "now": now,
            "lot": lot,
            "status": lot.out_time_status(now),
            "limit": lot.resolved_out_time_limit(),
            "expired": lot.shelf_life_expired(now),
            "pot_remaining": lot.pot_life_remaining(now),
            "events": lot.storage_events.all(),
            "kits": lot.kits.prefetch_related("parts").all(),
        },
    )


def cure_detail(request, pk):
    run = get_object_or_404(CureRun.objects.select_related("spec"), pk=pk)
    return render(
        request,
        "tracker/cure_detail.html",
        {
            "run": run,
            "evaluation": run.evaluate(),
            "missing": run.missing_required_fields(),
            "chart": cure_profile_html(run),
            "parts": run.parts.all(),
        },
    )


@require_POST
def draft_ncr(request, criterion_id):
    """Advisory: draft an editable NCR explanation for a criterion via Claude.

    Gated on ANTHROPIC_API_KEY (404 when disabled). Drafting persists nothing
    and does not change the criterion's computed readiness.
    """
    if not assist.is_enabled():
        raise Http404("Assist is disabled.")
    criterion = get_object_or_404(Criterion, criterion_id=criterion_id)
    result = evaluate_criterion(criterion, as_of=timezone.now())
    text = assist.draft_ncr_explanation(
        criterion.criterion_id, criterion.title, result.reason
    )
    return render(request, "tracker/_assist_draft.html", {"text": text})


def trace_index(request):
    return render(
        request,
        "tracker/trace_index.html",
        {"kits": Kit.objects.prefetch_related("lots__material", "parts__cure_run").all()},
    )
