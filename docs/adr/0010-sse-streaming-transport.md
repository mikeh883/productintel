# ADR 0010: Server-Sent Events for streaming agent output

**Status:** Accepted
**Date:** 2026-06-09

## Context

ADK agents emit events incrementally. The UI should show agent output as it is produced rather than after a full response completes. We need a transport for that across the web-to-agent boundary.

## Decision

The agent service streams events to the frontend over Server-Sent Events (SSE) layered on the FastAPI endpoints. Non-streaming requests stay as plain REST and JSON.

## Alternatives considered

- **WebSockets.** Bidirectional and powerful, but heavier than needed for a server-to-client event stream.
- **Polling for completion.** Simple, but high-latency and a poor agent experience that loses the live-progress feel.

## Consequences

- Live agent output in the UI, which fills a capability the original framework lacked.
- SSE is simple and HTTP-native.
- Any future bidirectional need would justify revisiting this in favor of WebSockets.
