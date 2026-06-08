"""Gated, advisory Claude assist client.

Gated at runtime on ``ANTHROPIC_API_KEY``: with no key the app is fully usable
and every entry point raises :class:`AssistDisabledError`. The assist drafts
human-editable text and paraphrased structure only — it never decides compliance
or computes a limit (those are the deterministic engines' job).
"""
import anthropic
from django.conf import settings
from pydantic import BaseModel

from . import prompts

MODEL = "claude-opus-4-8"


class AssistDisabledError(RuntimeError):
    """Raised when an assist function is called without an API key configured."""


class CriterionDraft(BaseModel):
    criterion_id: str
    title: str  # paraphrased
    section: str


class CriteriaImport(BaseModel):
    criteria: list[CriterionDraft]


def is_enabled() -> bool:
    return bool(settings.ANTHROPIC_API_KEY)


def _client() -> "anthropic.Anthropic":
    if not is_enabled():
        raise AssistDisabledError("ANTHROPIC_API_KEY is not set; assist is disabled.")
    return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _complete(system: str, user: str, max_tokens: int = 2000) -> str:
    """Return Claude's drafted text. Adaptive thinking; text blocks only."""
    message = _client().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in message.content if b.type == "text").strip()


def _parse(system: str, user: str, schema: type[BaseModel]) -> BaseModel:
    response = _client().messages.parse(
        model=MODEL,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
    )
    return response.parsed_output


def draft_ncr_explanation(criterion_id: str, title: str, reason: str) -> str:
    """Draft an editable NCR explanation. Advisory — opens/changes nothing."""
    return _complete(
        prompts.NCR_SYSTEM, prompts.ncr_user(criterion_id, title, reason)
    )


def draft_readiness_narrative(summary: str) -> str:
    """Draft an editable readiness-summary narrative. Advisory."""
    return _complete(prompts.NARRATIVE_SYSTEM, prompts.narrative_user(summary))


def import_criteria(text: str) -> list[dict]:
    """Structure a user-supplied AC7118 export into paraphrased criteria rows.

    Returns plain dicts (id/title/section) for the engineer to review before any
    are persisted — this function does not write to the database.
    """
    result = _parse(prompts.IMPORT_SYSTEM, prompts.import_user(text), CriteriaImport)
    return [c.model_dump() for c in result.criteria]
