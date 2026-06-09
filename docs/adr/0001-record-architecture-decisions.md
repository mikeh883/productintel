# ADR 0001: Record architecture decisions

**Status:** Accepted
**Date:** 2026-06-09

## Context

This project makes a number of stack and architecture choices that should be legible to anyone who reads the codebase, including a future collaborator or an interviewer. Decisions made implicitly tend to be forgotten, re-litigated, or impossible to explain later.

## Decision

We will capture significant architecture and stack decisions as Architecture Decision Records (ADRs): short, numbered markdown files in `docs/adr/`, each stating the context, the decision, the alternatives considered, and the consequences. One decision per file. ADRs are immutable once accepted; a later ADR supersedes an earlier one rather than editing it.

We use the format popularized by Michael Nygard. The template lives at `docs/adr/template.md`.

## Alternatives considered

- **No formal record.** Faster in the moment, but the reasoning is lost and decisions get silently reversed.
- **A single design doc.** Easier to skim, but it blurs distinct decisions together and loses the "why we did not do X" history.

## Consequences

- Every meaningful choice has a defensible, written rationale.
- The ADR set doubles as a portfolio artifact demonstrating deliberate technical decision-making.
- A small ongoing discipline: new significant decisions get a new ADR.
