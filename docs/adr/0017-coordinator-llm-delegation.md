# ADR 0017: Coordinator agent with LLM-driven delegation

**Status:** Accepted
**Date:** 2026-06-09

## Context

The Work slice adds a second specialist (a story-triage agent) alongside the
Knowledge agent. Something must decide which specialist handles each request.
ADK offers two composition primitives: `sub_agents`, where the framework injects
a `transfer_to_agent` tool and the LLM hands the conversation to a specialist,
and `AgentTool`, where one agent invokes another as an ordinary tool and keeps
control of the turn.

## Decision

A root `coordinator` agent owns the conversation and delegates via `sub_agents`
to `knowledge_agent` and `work_agent`. Routing is LLM-driven: the coordinator's
instruction describes each specialist, ADK appends transfer instructions and the
`transfer_to_agent` tool, and the model picks the target. Each specialist keeps
its own instruction, tools, and callback seam wiring (ADR 0016), so traces now
record which agent made every call.

The FastAPI Runner now serves the coordinator; the HTTP surface (ADR 0010) is
unchanged.

## Alternatives considered

- **AgentTool composition.** The coordinator would keep control and could merge
  both specialists' outputs in one answer. Rejected for this slice: it hides the
  delegation decision inside a tool call, and transfer is the primitive that
  matches how larger ADK systems are composed. AgentTool remains the right choice
  later for true mid-answer composition.
- **Routing in code (keyword or classifier).** Deterministic and cheap, but the
  point of this slice is to exercise ADK's native delegation; a code router would
  also need maintenance as specialists are added.
- **One agent with all tools.** Simplest, but instructions for unrelated domains
  degrade each other, and it abandons the multi-agent structure the roadmap is
  building toward.

## Consequences

- After a transfer, the specialist owns the rest of the turn, and follow-up turns
  resume with it until it transfers back. Sticky context is usually what a user
  wants mid-task; it also means the coordinator is not re-evaluating every turn.
- Each routed request costs one extra model call (the coordinator's routing
  decision) before the specialist starts.
- The trace table now shows multi-agent invocations end to end, which is exactly
  the observability the seam was built for.
