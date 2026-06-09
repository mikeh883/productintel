import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

from .agent import coordinator
from .config import settings

app = FastAPI(title="ProductIntel Agent Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# v0 uses in-memory sessions (ADR 0015). A DatabaseSessionService is the later upgrade.
session_service = InMemorySessionService()
runner = Runner(
    agent=coordinator,
    app_name=settings.app_name,
    session_service=session_service,
)

# v0 has no auth (ADR 0014), so all traffic is one synthetic user.
USER_ID = "local-user"


class ChatRequest(BaseModel):
    message: str
    session_id: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


async def _ensure_session(session_id: str) -> None:
    existing = await session_service.get_session(
        app_name=settings.app_name, user_id=USER_ID, session_id=session_id
    )
    if existing is None:
        await session_service.create_session(
            app_name=settings.app_name, user_id=USER_ID, session_id=session_id
        )


async def _event_stream(message: str, session_id: str):
    """Stream the agent's output as Server-Sent Events (ADR 0010)."""
    await _ensure_session(session_id)
    new_message = types.Content(role="user", parts=[types.Part(text=message)])

    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=new_message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                text = getattr(part, "text", None)
                if text:
                    yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(request.message, request.session_id),
        media_type="text/event-stream",
    )
