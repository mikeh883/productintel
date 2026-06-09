# ADR 0014: Defer authentication for v0; JWT bearer when introduced

**Status:** Accepted
**Date:** 2026-06-09

## Context

The first slice is a single-user learning artifact. Authentication adds drag and is not needed to exercise ADK. When it is added, the pattern should be generic and not vendor-locked.

## Decision

v0 ships without authentication. When auth is introduced, the frontend will obtain a token and the agent service (FastAPI) will validate a JWT bearer token on protected endpoints.

## Alternatives considered

- **Build full auth now.** Real drag for no learning gain at this stage.
- **A vendor-specific auth SDK end to end.** Faster later, but less translatable than the standard JWT-bearer pattern.

## Consequences

- v0 stays small and finishable.
- The chosen later pattern (frontend issues a token, backend validates a JWT) is the generic enterprise approach and easy to explain.
- A future ADR will record the specific identity provider when one is chosen.
