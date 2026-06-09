"""The work agent: files and triages backlog stories.

Tools are plain functions with docstrings (ADK builds their schemas), writing
through SQLAlchemy directly. All calls pass through the callback seam (ADR 0016),
so tool latency and result sizes are traced like every other agent.
"""

import uuid
from datetime import datetime, timezone

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from sqlalchemy import select

from . import seam
from .config import settings
from .db import SessionLocal
from .models import Story

STORY_TYPES = ("bug", "feature", "chore")
PRIORITIES = ("P0", "P1", "P2", "P3")


def _parse_story_id(story_id: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(story_id)
    except ValueError:
        return None


def _format_story(story: Story, include_body: bool = False) -> str:
    triage = (
        f"{story.story_type}/{story.priority}" if story.status == "triaged" else "untriaged"
    )
    line = f"{story.id} [{triage}] {story.title}"
    if include_body:
        line += f"\n{story.body}"
        if story.triage_rationale:
            line += f"\nTriage rationale: {story.triage_rationale}"
    return line


def create_story(title: str, body: str) -> str:
    """File a new story in the backlog (it starts untriaged).

    Args:
        title: A concise one-line summary of the report or request.
        body: The full text of the report or request, as provided.

    Returns:
        Confirmation with the new story's id.
    """
    with SessionLocal() as db:
        story = Story(title=title, body=body)
        db.add(story)
        db.commit()
        return f"Story filed: {story.id} [untriaged] {title}"


def list_stories(status: str = "untriaged") -> str:
    """List stories in the backlog.

    Args:
        status: Filter by 'untriaged', 'triaged', or 'all'.

    Returns:
        One story per line with id, triage state, and title.
    """
    if status not in ("untriaged", "triaged", "all"):
        return "Invalid status filter: use 'untriaged', 'triaged', or 'all'."
    with SessionLocal() as db:
        query = select(Story).order_by(Story.created_at)
        if status != "all":
            query = query.where(Story.status == status)
        stories = db.scalars(query).all()
        if not stories:
            return f"No {status} stories." if status != "all" else "The backlog is empty."
        return "\n".join(_format_story(s) for s in stories)


def get_story(story_id: str) -> str:
    """Read one story in full, including its body text.

    Args:
        story_id: The story's id (UUID), as shown by list_stories.

    Returns:
        The story's id, triage state, title, and full body.
    """
    key = _parse_story_id(story_id)
    if key is None:
        return f"'{story_id}' is not a valid story id; use the UUID shown by list_stories."
    with SessionLocal() as db:
        story = db.get(Story, key)
        if story is None:
            return f"No story with id {story_id}."
        return _format_story(story, include_body=True)


def triage_story(story_id: str, story_type: str, priority: str, rationale: str) -> str:
    """Triage a story: classify it and set its priority.

    Args:
        story_id: The story's id (UUID), as shown by list_stories.
        story_type: One of 'bug', 'feature', 'chore'.
        priority: One of 'P0' (critical: outage or data loss), 'P1' (urgent:
            badly broken for many users), 'P2' (important, scheduled), 'P3'
            (nice to have).
        rationale: One or two sentences explaining the classification and priority.

    Returns:
        Confirmation of the triage, or an error to correct.
    """
    if story_type not in STORY_TYPES:
        return f"Invalid story_type '{story_type}': use one of {', '.join(STORY_TYPES)}."
    if priority not in PRIORITIES:
        return f"Invalid priority '{priority}': use one of {', '.join(PRIORITIES)}."
    key = _parse_story_id(story_id)
    if key is None:
        return f"'{story_id}' is not a valid story id; use the UUID shown by list_stories."
    with SessionLocal() as db:
        story = db.get(Story, key)
        if story is None:
            return f"No story with id {story_id}."
        story.story_type = story_type
        story.priority = priority
        story.triage_rationale = rationale
        story.status = "triaged"
        story.triaged_at = datetime.now(timezone.utc)
        db.commit()
        return f"Triaged: {story.id} [{story_type}/{priority}] {story.title}"


INSTRUCTION = """You are the ProductIntel Work assistant. You manage the story backlog.

Filing: when the user reports a bug, requests a feature, or pastes a raw report,
call `create_story` with a concise title and the full text as the body. Never
invent stories the user did not provide.

Triage: to triage a story, read it (use `get_story` if you only have the list line),
then call `triage_story` with:
- story_type: bug (broken behavior), feature (new capability), chore (maintenance).
- priority: P0 critical outage or data loss; P1 urgent, badly broken for many
  users; P2 important, scheduled work; P3 nice to have.
- rationale: one or two sentences justifying both choices.
Be decisive: pick the single best type and priority even for vague reports, and
note the ambiguity in the rationale.

When asked to triage the backlog, list untriaged stories, triage each one, and
finish with a compact summary table of id, type, priority, and title."""


work_agent = LlmAgent(
    name="work_agent",
    description="Files and triages backlog stories: bugs, feature requests, and chores.",
    model=LiteLlm(model=settings.model),
    instruction=INSTRUCTION,
    tools=[create_story, list_stories, get_story, triage_story],
    before_model_callback=seam.before_model,
    after_model_callback=seam.after_model,
    before_tool_callback=seam.before_tool,
    after_tool_callback=seam.after_tool,
)
