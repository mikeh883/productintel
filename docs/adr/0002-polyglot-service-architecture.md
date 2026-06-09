# ADR 0002: Polyglot service architecture

**Status:** Accepted
**Date:** 2026-06-09

## Context

Google ADK is a Python agent runtime, not a web framework. It has no UI, routing, or auth of its own. The product still needs a user interface, persistence, and an agent layer, so we must decide how those pieces fit together.

## Decision

We will build a polyglot, service-oriented system with three parts: a TypeScript/Next.js frontend, a separate Python service that hosts the ADK agents behind an HTTP API, and a PostgreSQL database as the shared system of record. The frontend never imports agent code; it talks to the agent service over HTTP.

## Alternatives considered

- **Single full-stack Python app** (FastAPI with server-rendered templates or a Python UI framework). Keeps one language but discards a mature React frontend and design system, and Python web UIs are weaker than the React ecosystem.
- **Agents embedded in a Node/TypeScript backend** (as the original productbrain did with AgentWeave). Keeps one language, but it means not using ADK, which is the entire point of the rebuild.

## Consequences

- Two runtimes to develop, run, and deploy.
- A clear, enterprise-typical seam between the web and agent tiers, which is where much of the learning value lives.
- Contracts between the tiers must be explicit (see ADR 0005 for the API and ADR 0010 for streaming).
