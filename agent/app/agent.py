import os

# We route models through LiteLLM deliberately for provider portability (ADR 0006);
# silence ADK's nudge toward native Gemini.
os.environ.setdefault("ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS", "true")

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from . import seam
from .config import settings
from .retrieval import search
from .work import work_agent


def search_knowledge(query: str) -> str:
    """Search the knowledge base for passages relevant to the query.

    Args:
        query: A natural-language description of what to look for.

    Returns:
        Formatted passages with their source document titles, or a note if nothing
        relevant was found.
    """
    hits = search(query, k=5)
    if not hits:
        return "No relevant passages found in the knowledge base."
    blocks = [f"[{i}] {hit.title}\n{hit.content}" for i, hit in enumerate(hits, start=1)]
    return "\n\n".join(blocks)


INSTRUCTION = """You are the ProductIntel Knowledge assistant.

Answer questions using only the knowledge base. Always call the `search_knowledge`
tool before answering a factual question, and cite the document titles you relied on.
If the knowledge base does not contain the answer, say so plainly rather than guessing."""


# Model is wrapped in LiteLlm so the provider is swappable (ADR 0006).
# All model and tool calls pass through the callback seam (ADR 0016).
knowledge_agent = LlmAgent(
    name="knowledge_agent",
    description="Answers questions from the product knowledge base, with citations.",
    model=LiteLlm(model=settings.model),
    instruction=INSTRUCTION,
    tools=[search_knowledge],
    before_model_callback=seam.before_model,
    after_model_callback=seam.after_model,
    before_tool_callback=seam.before_tool,
    after_tool_callback=seam.after_tool,
)


COORDINATOR_INSTRUCTION = """You are the ProductIntel coordinator. Route each request
to the right specialist instead of answering domain questions yourself:

- knowledge_agent: questions about the product or its documentation, anything
  answerable from the knowledge base.
- work_agent: anything about the backlog or stories, including filing bug reports,
  feature requests, listing stories, and triage.

Answer directly only for trivial conversation such as greetings. If a request is
ambiguous, pick the more likely specialist rather than asking."""


# The first multi-agent composition (ADR 0017): a coordinator that delegates via
# ADK's sub_agents transfer. ADK injects a `transfer_to_agent` tool automatically;
# after a transfer the specialist owns the rest of the turn, and follow-up turns
# resume with it until it transfers back.
coordinator = LlmAgent(
    name="coordinator",
    description="Routes requests to the knowledge or work specialist.",
    model=LiteLlm(model=settings.model),
    instruction=COORDINATOR_INSTRUCTION,
    sub_agents=[knowledge_agent, work_agent],
    before_model_callback=seam.before_model,
    after_model_callback=seam.after_model,
    before_tool_callback=seam.before_tool,
    after_tool_callback=seam.after_tool,
)
