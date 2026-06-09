# ADR 0009: Reuse Next.js for the frontend

**Status:** Accepted
**Date:** 2026-06-09

## Context

The original project has a mature Next.js, React, and Tailwind frontend with an established design system. The learning goal of this rebuild is the agent backend and the web-to-agent seam, not the frontend.

## Decision

We will build the frontend in Next.js (App Router) with React, TypeScript, and Tailwind, reusing patterns and design tokens from the original where useful.

## Alternatives considered

- **A new or different frontend framework.** More breadth of learning, but it spends effort where we are already competent and slows the project.
- **A Python-rendered UI.** Keeps the system in one language but produces a weaker product and abandons the design system.

## Consequences

- Frontend work is fast and familiar, concentrating new learning on ADK and the seam.
- The system remains polyglot, consistent with ADR 0002.
