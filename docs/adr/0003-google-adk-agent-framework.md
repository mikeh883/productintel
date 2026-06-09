# ADR 0003: Google ADK as the agent framework

**Status:** Accepted
**Date:** 2026-06-09

## Context

We need an agent orchestration framework. The original project used a bespoke framework (AgentWeave). The goal of this rebuild is to learn and demonstrate industry-standard tooling, and ADK is in production use at the author's employer.

## Decision

We will use Google's Agent Development Kit (ADK) for all agent definition, tool use, orchestration, sessions, memory, and callbacks.

## Alternatives considered

- **AgentWeave** (the home-grown framework). Already understood; continuing it re-buys knowledge already gained and does not transfer to other teams.
- **LangGraph / LangChain.** Strong and provider-neutral, but requires more assembly and is not the specific tool we want fluency in.

## Consequences

- Agent code becomes code-first (ADK convention) rather than data-first (AgentWeave's registry rows). This is a deliberate reversal of the original architecture.
- We gain real function-calling, workflow agents, sessions, memory, and callbacks out of the box.
- We take a soft dependency on ADK's conventions. Model lock-in specifically is mitigated by ADR 0006.
