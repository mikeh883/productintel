# ADR 0005: FastAPI as the API layer

**Status:** Accepted
**Date:** 2026-06-09

## Context

The agent service must expose ADK agents to the frontend over HTTP, with streaming, request validation, and documentation.

## Decision

We will serve the ADK agents behind FastAPI, exposing a small and explicit set of endpoints. ADK integrates with FastAPI directly.

## Alternatives considered

- **Flask.** Simpler, but synchronous by default and weaker on typing, streaming, and OpenAPI generation.
- **Django REST Framework.** Heavier, and brings an ORM and conventions we do not need alongside ADK.

## Consequences

- Async support for streaming (see ADR 0010), Pydantic validation, and automatic OpenAPI docs.
- A ubiquitous, instantly recognizable choice that pairs naturally with ADK.
