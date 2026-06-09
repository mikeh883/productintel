# Knowledge Module

The Knowledge module is the first vertical slice of ProductIntel. It provides
retrieval-augmented chat over a corpus of documents.

## How it works

A user asks a question in the chat UI. The question is sent to the agent service, which
runs a single ADK agent. The agent has one tool, `search_knowledge`, that embeds the
question and retrieves the most similar document chunks from the database. The agent
reads those passages and composes an answer, citing the documents it used. If nothing
relevant is found, the agent says so rather than guessing.

## Ingestion

Documents are added by running the ingest script over a directory of Markdown files.
Each file is chunked by paragraph, each chunk is embedded, and the chunks and their
vectors are written to the database. Re-running ingestion adds documents; it does not
deduplicate, which is a known limitation of the first slice.

## What comes next

The second slice introduces Work: story triage. That is where the first multi-agent
coordination appears, with one agent routing between answering from knowledge and acting
on work items.
