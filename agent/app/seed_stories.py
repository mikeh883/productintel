"""Seed a demo backlog of raw, untriaged stories.

Run with: python -m app.seed_stories (or `make seed` from the repo root).
Idempotent: does nothing if any stories already exist.

The samples vary deliberately in quality and urgency so triage has real work
to do: an outage, an obvious feature request, a vague complaint, and so on.
"""

from sqlalchemy import func, select

from .db import SessionLocal
from .models import Story

SEED_STORIES = [
    (
        "Agent container crash-loops after database restart",
        "Restarted the database container to apply a config change and the agent "
        "service never recovered: it crash-loops with connection errors until "
        "manually restarted. Chat is completely down while this happens.",
    ),
    (
        "Chat page spins forever when the agent service is down",
        "If the agent service is not running, the web chat just shows the typing "
        "indicator forever. No error message, no timeout. Users think the product "
        "is hanging.",
    ),
    (
        "Export trace events as CSV",
        "It would be useful to download the trace_events data as a CSV so I can "
        "analyze token spend in a spreadsheet without connecting to Postgres.",
    ),
    (
        "Re-running ingest duplicates every document",
        "Ran the corpus ingest twice and now every search result appears twice. "
        "Looks like there is no dedupe on ingest, so each run inserts a fresh "
        "copy of every document and chunk.",
    ),
    (
        "Search feels off lately",
        "Not sure how to describe it, but answers seem to cite the wrong document "
        "sometimes. Could be the search, could be the model. Someone should look "
        "into it.",
    ),
    (
        "Pin Python dependency versions in pyproject",
        "Several dependencies in the agent service are unpinned. We have already "
        "been bitten by upstream changes once; pin the versions we have verified "
        "against so builds are reproducible.",
    ),
]


def main() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(func.count()).select_from(Story))
        if existing:
            print(f"Stories table already has {existing} rows; not seeding.")
            return
        for title, body in SEED_STORIES:
            db.add(Story(title=title, body=body))
        db.commit()
        print(f"Seeded {len(SEED_STORIES)} untriaged stories.")


if __name__ == "__main__":
    main()
