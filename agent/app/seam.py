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

Langfuse contract (verified against langfuse 4.7.1): observations created with
an explicit trace_context land in that trace; create_trace_id(seed=...) is
deterministic, so one invocation = one trace; propagate_attributes stamps
session.id on observations created inside its context; export runs on a
background thread and degrades to logged warnings if the host is unreachable.
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

# Open Langfuse observations, keyed like the start dicts: started in before_*,
# ended in after_*. None client = exporter off (no keys configured).
_langfuse: Optional[Langfuse] = (
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    if settings.langfuse_public_key and settings.langfuse_secret_key
    else None
)
_model_observations: dict[str, Any] = {}
_tool_observations: dict[str, Any] = {}

# Cap prompt/result payloads sent to Langfuse; full text stays available locally.
LANGFUSE_PAYLOAD_CHARS = 4_000


def _excerpt(value: Any) -> str:
    text = str(value)
    if len(text) > LANGFUSE_PAYLOAD_CHARS:
        return text[:LANGFUSE_PAYLOAD_CHARS] + " ...[truncated for export]"
    return text


def _last_message_text(llm_request: LlmRequest) -> str:
    for content in reversed(llm_request.contents or []):
        texts = [part.text for part in (content.parts or []) if getattr(part, "text", None)]
        if texts:
            return _excerpt(" ".join(texts))
    return ""


def _response_text(llm_response: LlmResponse) -> str:
    if llm_response.content and llm_response.content.parts:
        texts = [part.text for part in llm_response.content.parts if getattr(part, "text", None)]
        if texts:
            return _excerpt(" ".join(texts))
    return ""


def _trace_context(invocation_id: str) -> dict[str, str]:
    # Deterministic: every callback in one ADK invocation joins the same trace.
    return {"trace_id": Langfuse.create_trace_id(seed=invocation_id)}

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
                with propagate_attributes(session_id=callback_context.session.id):
                    _langfuse.create_event(
                        trace_context=_trace_context(callback_context.invocation_id),
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
    if _langfuse:
        try:
            with propagate_attributes(
                session_id=callback_context.session.id, trace_name="chat-turn"
            ):
                _model_observations[callback_context.invocation_id] = _langfuse.start_observation(
                    trace_context=_trace_context(callback_context.invocation_id),
                    as_type="generation",
                    name=f"{callback_context.agent_name}.model",
                    input=_last_message_text(llm_request),
                )
        except Exception as exc:
            print(f"[seam] langfuse generation start failed: {exc}")
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

    observation = _model_observations.pop(callback_context.invocation_id, None)
    if observation is not None:
        try:
            observation.update(
                model=llm_response.model_version or settings.model,
                usage_details={"input": input_tokens, "output": output_tokens},
                output=_response_text(llm_response),
                metadata={
                    "finish_reason": str(llm_response.finish_reason),
                    "session_tokens_used": str(used),
                },
            )
            observation.end()
        except Exception as exc:
            print(f"[seam] langfuse generation end failed: {exc}")

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
    key = f"{tool_context.invocation_id}:{tool.name}"
    _tool_starts[key] = time.monotonic()
    if _langfuse:
        try:
            with propagate_attributes(session_id=tool_context.session.id):
                _tool_observations[key] = _langfuse.start_observation(
                    trace_context=_trace_context(tool_context.invocation_id),
                    as_type="tool",
                    name=tool.name,
                    input=_excerpt(args),
                    metadata={"agent": tool_context.agent_name},
                )
        except Exception as exc:
            print(f"[seam] langfuse tool start failed: {exc}")
    return None


async def after_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    key = f"{tool_context.invocation_id}:{tool.name}"
    start = _tool_starts.pop(key, None)
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

    observation = _tool_observations.pop(key, None)
    if observation is not None:
        try:
            observation.update(
                output=_excerpt(result_repr),
                metadata={"result_chars": str(len(result_repr)), "truncated": str(truncated)},
            )
            observation.end()
        except Exception as exc:
            print(f"[seam] langfuse tool end failed: {exc}")

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
