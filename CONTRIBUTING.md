# Contributing

This is a personal portfolio and learning project, developed in the open. You are
welcome to read it, open an issue with a question or suggestion, or fork it. It is not
actively seeking contributors, so please open an issue to discuss before sending a pull
request.

## How the project is organized

- `web/` and `agent/` are independent services with their own toolchains (see
  [README](README.md) for the architecture).
- Significant decisions are recorded as Architecture Decision Records in
  [`docs/adr/`](docs/adr/). If you propose a change that alters a recorded decision, add
  a new ADR rather than editing an accepted one.

## Development setup

See [Getting started](README.md#getting-started). The agent service has its own notes,
including ADK version considerations, in [`agent/README.md`](agent/README.md).

## Conventions

- Python: keep the agent service typed and formatted consistently with the existing
  code.
- Commits: small, focused, and described in the imperative mood.
