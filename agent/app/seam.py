"""The callback seam (ADR 0016): observability and enforced guardrails.

Every model call and tool call passes through these hooks. This is where
policy *executes* — token budgets block, oversized tool results get cut —
rather than living as advisory prompt text. It is also the single place
where tracing plugs in: the local trace_events table always, and Langfuse
(ADR 0013) when keys are configured.

ADK callback contract (verified against google-adk 2.2.0):
  before_model(ctx, request)  -> None to proceed | LlmResponse to short-circuit
  after_model(ctx, response)  -> None | replacement LlmResponse
  before_tool(tool, args, ctx) -> None to proceed | dict to skip tool with result
  after_tool(tool, args, ctx, result) -> None | replacement dict

Langfuse export (verified against langfuse 4.7.1, ADR 0013): constructing the
Langfuse client registers a global OpenTelemetry tracer provider, which ADK's
native instrumentation (scope 'gcp.vertex.agent') exports through automatically:
one nested trace per invocation (invoke_agent -> call_llm / execute_tool), with
token usage attached. LiteLLM's duplicate spans (scope 'litellm') are blocked so
tokens are not double-counted. The seam's own export role is what ADK cannot
know: stamping the chat session id onto the trace (propagate_attributes sets it
on the currently active ADK span) and emitting guardrail events. Export runs on
a background thread and degrades to logged warnings if the host is unreachable.
"""

import asyncio
import time
from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from langfuse import Langfuse, propagate_attributes

from .config import settings
from .db import SessionLocal
from .models import TraceEvent

TOKENS_USED_KEY = "seam:tokens_used"

# Wall-clock starts, keyed by invocation id. Module-level rather than session
# state because timing is process-local scratch, not conversational state.
_model_starts: dict[str, float] = {}
_tool_starts: dict[str, float] = {}

# None client = exporter off (no keys configured). Constructing the client is
# what turns on export of ADK's native spans (see module docstring).
_langfuse: Optional[Langfuse] = (
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url,
        # ADK 2.2 emits each model call twice while it migrates to the GenAI
        # semantic conventions: a legacy 'call_llm' span and a semconv
        # 'generate_content {model}' span with the same usage. Export only one
        # or Langfuse double-counts tokens. call_llm is kept because it parents
        # under invoke_agent, preserving the per-agent hierarchy in the UI.
        should_export_span=lambda span: not span.name.startswith("generate_content"),
    )
    if settings.langfuse_public_key and settings.langfuse_secret_key
    else None
)


def _stamp_session(session_id: str) -> None:
    """Mark the currently active ADK span (and the trace) with the chat session."""
    if _langfuse is None:
        return
    try:
        with propagate_attributes(session_id=session_id, trace_name="chat-turn"):
            pass
    except Exception as exc:  # tracing must never break the agent
        print(f"[seam] langfuse session stamp failed: {exc}")

BUDGET_EXHAUSTED_MESSAGE = (
    "This session has reached its token budget and cannot make further model "
    "calls. Start a new session to continue."
)


def _record(event: TraceEvent) -> None:
    with SessionLocal() as db:
        db.add(event)
        db.commit()


async def _record_async(event: TraceEvent) -> None:
    # The DB write is sync SQLAlchemy; keep it off the event loop.
    try:
        await asyncio.to_thread(_record, event)
    except Exception as exc:  # tracing must never break the agent
        print(f"[seam] trace write failed: {exc}")


async def before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    used = callback_context.state.get(TOKENS_USED_KEY, 0)
    if used >= settings.session_token_budget:
        await _record_async(
            TraceEvent(
                session_id=callback_context.session.id,
                invocation_id=callback_context.invocation_id,
                kind="guardrail",
                name="token_budget",
                detail={"tokens_used": used, "budget": settings.session_token_budget},
            )
        )
        if _langfuse:
            try:
                # No trace_context: the event nests into ADK's active trace.
                _langfuse.create_event(
                    name="token_budget_exhausted",
                    level="WARNING",
                    metadata={"tokens_used": str(used), "budget": str(settings.session_token_budget)},
                )
            except Exception as exc:  # tracing must never break the agent
                print(f"[seam] langfuse event failed: {exc}")
        return LlmResponse(
            content=types.Content(
                role="model", parts=[types.Part(text=BUDGET_EXHAUSTED_MESSAGE)]
            )
        )

    _model_starts[callback_context.invocation_id] = time.monotonic()
    _stamp_session(callback_context.session.id)
    return None


async def after_model(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    # Streaming emits partial responses; only the final one carries usage.
    usage = llm_response.usage_metadata
    if usage is None or llm_response.partial:
        return None

    start = _model_starts.pop(callback_context.invocation_id, None)
    duration_ms = int((time.monotonic() - start) * 1000) if start else None

    input_tokens = usage.prompt_token_count or 0
    output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)

    used = callback_context.state.get(TOKENS_USED_KEY, 0) + input_tokens + output_tokens
    callback_context.state[TOKENS_USED_KEY] = used

    await _record_async(
        TraceEvent(
            session_id=callback_context.session.id,
            invocation_id=callback_context.invocation_id,
            kind="model",
            name=llm_response.model_version or settings.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            detail={
                "session_tokens_used": used,
                "budget": settings.session_token_budget,
                "finish_reason": str(llm_response.finish_reason),
            },
        )
    )
    return None


async def before_tool(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> Optional[dict]:
    _tool_starts[f"{tool_context.invocation_id}:{tool.name}"] = time.monotonic()
    _stamp_session(tool_context.session.id)
    return None


async def after_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    start = _tool_starts.pop(f"{tool_context.invocation_id}:{tool.name}", None)
    duration_ms = int((time.monotonic() - start) * 1000) if start else None

    # Cost-control cap: never let a tool flood the context window. This is
    # the ADK descendant of AgentWeave's summaries-plus-pointers pattern.
    truncated = False
    replacement: Optional[dict] = None
    result_repr = str(tool_response)
    if len(result_repr) > settings.max_tool_result_chars:
        truncated = True
        replacement = {
            "result": result_repr[: settings.max_tool_result_chars],
            "note": (
                f"[truncated by the callback seam at {settings.max_tool_result_chars} "
                "chars — narrow the query to retrieve less at once]"
            ),
        }

    await _record_async(
        TraceEvent(
            session_id=tool_context.session.id,
            invocation_id=tool_context.invocation_id,
            kind="tool",
            name=tool.name,
            duration_ms=duration_ms,
            detail={
                "args_chars": len(str(args)),
                "result_chars": len(result_repr),
                "truncated": truncated,
            },
        )
    )
    return replacement
