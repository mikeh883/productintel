# ADR 0004: Python 3.12 and uv for the agent service

**Status:** Accepted
**Date:** 2026-06-09

## Context

The agent service is Python, because ADK requires it. We need a dependency and environment manager.

## Decision

We will target Python 3.12 or later and use uv for dependency resolution, virtual environments, and lockfiles.

## Alternatives considered

- **Poetry.** Mature and widely used, but slower and heavier than uv.
- **pip + venv + requirements.txt.** The lowest common denominator, with weak locking and environment ergonomics.

## Consequences

- Fast, reproducible installs backed by a lockfile.
- uv is relatively new, so a contributor may need a one-time install, but it is simple to explain and increasingly standard.
