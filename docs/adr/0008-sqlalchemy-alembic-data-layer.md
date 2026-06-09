# ADR 0008: SQLAlchemy 2.0 and Alembic for data access

**Status:** Accepted
**Date:** 2026-06-09

## Context

The Python agent service needs typed database access and a way to version schema changes.

## Decision

We will use SQLAlchemy 2.0 (typed ORM and core) for queries and Alembic for migrations.

## Alternatives considered

- **SQLModel.** More ergonomic and pairs with FastAPI (same author), but it is a thinner layer over SQLAlchemy and less prevalent in enterprises. A reasonable swap if boilerplate becomes a drag.
- **Raw SQL via asyncpg.** Maximum control, but hand-rolled migrations and result mapping.

## Consequences

- The data layer matches what most Python shops run, which serves the translatability goal.
- Alembic provides versioned, reviewable migrations.
- More verbose than SQLModel.
