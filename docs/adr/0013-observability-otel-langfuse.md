# ADR 0013: OpenTelemetry and Langfuse for observability via ADK callbacks

**Status:** Accepted
**Date:** 2026-06-09

## Context

LLM systems are hard to debug without tracing token usage, latency, prompts, and tool calls. The author specifically wants to build fluency in inference observability. ADK callbacks provide hook points around model and tool calls.

## Decision

We will instrument the agent service with OpenTelemetry and send LLM traces to Langfuse, wired through ADK's callback layer. This callback layer is also the intended home for guardrails and for the cost-control pointer pattern carried over from the original framework.

## Alternatives considered

- **Log lines only, no tracing.** Cheapest, but blind to cost and behavior.
- **A single-vendor LLM-ops SDK with no OpenTelemetry.** Less portable than an OpenTelemetry-based approach.

## Consequences

- Traceable, cost-aware agents, and a single well-placed seam (callbacks) for cross-cutting concerns.
- Not required for the very first slice; the callback seam is left open from the start and wiring may be deferred (see ADR 0015).
- Adds dependencies when enabled.
