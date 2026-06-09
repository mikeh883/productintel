# ProductIntel Architecture

ProductIntel is a polyglot, service-oriented system. It has three parts: a Next.js
frontend, a Python agent service built on Google's Agent Development Kit (ADK), and a
PostgreSQL database that serves as the system of record.

## Why a separate agent service

ADK is a Python agent runtime, not a web framework. It has no UI, routing, or auth of
its own. Rather than force the whole product into Python, the frontend stays in the
React ecosystem and talks to the agent service over HTTP. The interesting engineering
lives in the seam between the two: streaming agent output to the browser, and the
callback layer where observability and guardrails plug in.

## Data model

Knowledge is stored as documents and chunks. Each document is split into chunks, each
chunk is embedded into a vector, and the vectors live in PostgreSQL via the pgvector
extension. Retrieval is a cosine-similarity search over those vectors. Keeping the
relational data and the embeddings in one database avoids a separate vector store and
the synchronization problem that comes with it.

## Streaming

Agent responses are streamed to the UI using Server-Sent Events. The agent emits events
as it works, the agent service forwards them as an SSE stream, and the frontend renders
tokens as they arrive instead of waiting for a complete response.
