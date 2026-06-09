# ADR 0015: Knowledge as the first vertical slice

**Status:** Accepted
**Date:** 2026-06-09

## Context

The original product spans many modules. Building all of them on a new stack at once is the failure mode we want to avoid. We need a first slice small enough to finish but rich enough to exercise ADK meaningfully.

## Decision

The first vertical slice is Knowledge: retrieval-augmented chat over a document corpus, implemented as a single ADK agent with a pgvector-backed retrieval tool, surfaced as a streaming chat UI. Work (story triage) is the planned second slice and introduces the first multi-agent coordination.

## Alternatives considered

- **Start with Knowledge and Work together.** More surface area, but slower to a working artifact and harder to keep focused.
- **Start with a CRUD-heavy module** (for example a plain Work backlog). Would build a web app that barely uses ADK, defeating the purpose of the project.

## Consequences

- The first deliverable puts a real agent at the center and is finishable within the near-term window.
- It exercises ADK agents, tools, retrieval, and streaming end to end.
- Multi-agent patterns (workflow agents, delegation) wait for the second slice.
