# ADR 0012: Docker and Compose for packaging and local development

**Status:** Accepted
**Date:** 2026-06-09

## Context

A polyglot system (Node frontend, Python agent service, Postgres) needs a reproducible way to run locally and a portable unit to deploy.

## Decision

Each service ships a Dockerfile. A top-level `docker-compose.yml` runs Postgres and the agent service, and optionally the web app, for local development.

## Alternatives considered

- **Native local installs** of each runtime and Postgres. Fast for a solo developer but brittle and hard to reproduce.
- **Kubernetes from the start.** Real overkill at this stage.

## Consequences

- One command brings the stack up locally.
- Containers are the portable unit, deployable to any container host (Cloud Run, Render, Fly, and others).
- Some upfront Dockerfile work is required.
