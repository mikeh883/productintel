# ADR 0006: LiteLLM for provider-agnostic model access

**Status:** Accepted
**Date:** 2026-06-09

## Context

ADK is Gemini-native but can call other providers. We want to avoid locking the system to a single LLM vendor, and we want to keep parity with the original project's use of Claude possible.

## Decision

We will route model calls through LiteLLM so that agents target a model abstraction rather than a hardcoded provider. Both Gemini and Claude are treated as first-class.

## Alternatives considered

- **Gemini-native only.** Simplest setup, but vendor-locked and a weaker portability story.
- **Direct per-provider SDK wiring.** More control, but more code, and it reinvents what LiteLLM already provides.

## Consequences

- One configuration surface for models and easy provider switching.
- A clear demonstration of portable, vendor-neutral design.
- A thin extra dependency sits between ADK and the providers.
