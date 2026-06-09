from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .config import settings
from .retrieval import search


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
knowledge_agent = LlmAgent(
    name="knowledge_agent",
    model=LiteLlm(model=settings.model),
    instruction=INSTRUCTION,
    tools=[search_knowledge],
)
