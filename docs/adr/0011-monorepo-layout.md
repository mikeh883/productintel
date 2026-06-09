# ADR 0011: Monorepo layout

**Status:** Accepted
**Date:** 2026-06-09

## Context

The system has two deployable units (the web frontend and the agent service) plus shared documentation. We must decide how to structure the repository.

## Decision

We will use a single repository with top-level `web/` (Next.js) and `agent/` (Python ADK and FastAPI) directories, plus `docs/`. Each service keeps its own toolchain inside its directory.

## Alternatives considered

- **Two separate repositories.** Cleaner deploy boundaries, but it splits the story, complicates cross-cutting changes, and is worse for a portfolio reader who wants to see the whole system at once.
- **A heavier monorepo toolchain** (Nx, Turborepo). Overkill for two services in two languages.

## Consequences

- The whole system is browsable in one place, which suits a public portfolio repository.
- The two services keep independent toolchains.
- CI must be scoped per directory.
