# Why I Rebuilt ProductIntel on Google's Agent Development Kit

*June 2026. Draft for review. This is the decision story behind this repository; the formal record lives in the [ADRs](adr/).*

I spent the spring building ProductIntel, an AI-native operations platform, as a learning project. Along the way I built my own agent framework, because in early 2026 that was how you learned how agent systems actually work. The framework, AgentWeave, ran 21 agents across a product pipeline, a security scanner, a research feed, and an autonomous dev loop that turned backlog stories into pull requests.

Then I started using Google's Agent Development Kit at work, and I had to be honest with myself about what AgentWeave was for. It was never going to be a framework other people adopted. Its value was that building it taught me agent orchestration from the inside: context scoping, cost control, pipeline composition, the failure modes nobody writes about. That value was fully banked. Continuing to extend my own framework would have been re-buying knowledge I already owned, while the industry consolidated on tooling I had never touched.

So this repository is a rebuild. Same product thesis, new substrate, and a deliberate rule: every choice should be one that any engineering team would recognize, with the reasoning written down. There are sixteen Architecture Decision Records in `docs/adr/` and this essay is the narrative that connects them.

## The fork that matters: data-first vs code-first

The deepest difference between AgentWeave and ADK is not a feature list. It is a philosophical fork about what an agent *is*.

In AgentWeave, an agent was a row in a database: a slug, a system prompt, a model id, a list of allowed tools. The runtime was two functions that loaded the row, made exactly one LLM call, and wrote the output as a Markdown artifact. Tools were never passed to the model. The harness called them, the model never acted on its own, and every run was a bounded "read context, write artifact" step. That design bought three things I still believe in: predictable cost, runtime customization without redeploys, and a system simple enough to hold in your head.

In ADK, an agent is code: a model, an instruction, and tools the model can actually call. When a request comes in, the model decides whether to search, what to search for, and when it has enough to answer. That loop, the model acting instead of just generating, is the capability gap I could never close with prompt engineering in the old design. It is also a cost and safety surface that the old design simply did not have, which is why half of this rebuild is about putting that surface under control.

Neither side of the fork is "right." AgentWeave optimized for cost, simplicity, and customizability. ADK optimizes for capability and autonomy. The rebuild is partly an exercise in feeling that trade from both sides, and the parts of the old design worth keeping came along, as code this time.

## ADK is a runtime, not a web framework

The first architectural consequence of choosing ADK is one the marketing does not dwell on: ADK has no UI, no routing, no auth. It is a Python agent runtime. "Rebuild the product on ADK" therefore cannot mean what "rebuild it in another web framework" would mean.

ProductIntel v2 is a small polyglot system: a Next.js frontend, a Python service hosting the ADK agents behind FastAPI, and PostgreSQL with pgvector as the single store for both relational data and embeddings. The frontend never imports agent code. It talks to the agent service over HTTP and renders a stream.

I now think the seam between those services is where most of the transferable learning lives. Streaming agent events to a browser over SSE, deciding what crosses the boundary, and wiring policy into the runtime's callback layer are the problems every team shipping agents inside a real product has to solve, regardless of framework. A monolith would have hidden that seam from me.

## What v1 taught that v2 keeps

Three lessons crossed the rebuild intact, and watching them change shape was the most instructive part.

**Knowledge is the context engine.** In v1 I learned, slowly and with eval baselines to prove it, that the knowledge base is not a feature. It is the substrate that makes every AI feature work. So the first vertical slice of v2 is Knowledge: retrieval-augmented chat over a document corpus, with citations, built as one ADK agent with one pgvector-backed search tool. It answers from the corpus, cites which documents it used, and declines to answer what the corpus does not contain.

**Pass pointers, not payloads.** AgentWeave's signature cost pattern was that agents exchanged summaries plus IDs, and fetched full content only when genuinely needed. ADK does not prescribe anything like that; its instinct is to accumulate context. The pattern survives in v2 as a callback that caps oversized tool results before they reach the model, with a note telling the agent to narrow its query. Same idea, new enforcement point.

**Every call logs its tokens.** v1 logged every LLM call to a runs table, and that discipline paid for itself every time something got slow or expensive. v2 does the same through a `trace_events` table: every model call records tokens, latency, and finish reason; every tool call records latency and result size. One chat turn reads like a story in SQL: the first model call decides to search, the tool runs, the second model call composes the cited answer, and the session's cumulative token count ticks up alongside.

## The upgrade I cared most about: guardrails that execute

In v1, guardrails were Markdown injected into prompts. Advisory. A model can ignore prose, and a budget stated in English cannot stop an API call.

ADK's callback layer fixes the category error. Callbacks are code that runs before and after every model call and every tool call, and they can short-circuit. In v2, each session has a token budget held in session state. When a session crosses it, the `before_model` callback returns a response directly and the provider is never called. In the verification test, a deliberately tiny budget let the first call through, blocked the second, and wrote a guardrail event to the trace table with the arithmetic that justified the block.

I keep coming back to a line from the v1 build: humans can act on intent, agents need contracts. The callback seam is that idea with teeth. Policy moved from the prompt, where it was a hope, into the runtime, where it is a fact. This single change is, to me, the strongest argument for running on a framework with a real callback surface.

## The stack validated itself twice on day one

I wrote the model-access decision (ADR 0006) before any of this happened: route all model calls through LiteLLM so the provider is a configuration string, not a code path.

On the first live run, it turned out Google had retired both of the scaffold's default models, the embedding model and the chat model, in the weeks between my training data and that evening. The fix was two config strings and an explicit dimensions parameter. The same day, Anthropic shipped a new frontier model, and "should we use it" was a pricing question rather than an integration project. Two provider events in one day, zero architecture changes. Model IDs are perishable; the decision record explaining why they are config now has receipts.

## Honest limitations

This is a learning project and a thin slice, and pretending otherwise would defeat the point.

- Streaming is real but chunky. ADK currently emits the post-tool-loop answer as one event rather than token-level deltas; true incremental streaming is a planned refinement, not a done thing.
- Ingestion does not deduplicate. Re-running it adds documents again.
- There is no auth yet, by recorded decision (ADR 0014), and observability export to Langfuse is a planned attachment to the existing seam, not yet wired (ADR 0013).
- The corpus is two documents. The slice proves the path, not the scale.

## What I'd tell another builder

If you built your own agent framework in 2024 or 2025, you did not waste your time. You bought intuitions that people who started on frameworks do not have: you know *why* sessions exist, why callback seams matter, what context discipline costs when you skip it. But the moment those intuitions are banked, the marginal lesson from extending your own framework drops below the marginal lesson from rebuilding on what the industry actually runs. The rebuild itself is the best comparison study you will ever do, because every primitive you meet, you can ask: what did my version of this look like, and which design was right?

I am still building fluency with ADK, and the next slice, a work-triage agent that introduces real multi-agent delegation, will test primitives I have only read about so far. The ADRs will keep the record honest.

*The full decision set is in [`docs/adr/`](adr/). The original project, framework and all, remains separate as the v1 line.*
