# ADR 0007: PostgreSQL and pgvector as the single datastore

**Status:** Accepted
**Date:** 2026-06-09

## Context

We need relational storage (artifacts, metadata) and vector storage (embeddings for retrieval). The original project established that pgvector is sufficient for this corpus size.

## Decision

PostgreSQL is the single system of record, with the pgvector extension for embeddings. We will not add a separate vector database until scale demands it.

## Alternatives considered

- **Postgres plus a dedicated vector DB** (Pinecone, Weaviate, Qdrant). More capable at very large scale, but adds an operational component and a synchronization problem we do not yet have.
- **A vector-only store.** Loses relational integrity for the rest of the data.

## Consequences

- One database to run, back up, and reason about.
- Transactional consistency between artifacts and their embeddings.
- A defensible "do not add infrastructure until you need it" stance. Revisit if corpus size or latency outgrows pgvector.
