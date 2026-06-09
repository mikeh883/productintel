// Proxies chat requests to the Python agent service and streams the SSE
// response straight back to the browser (ADR 0002 seam, ADR 0010 streaming).

export const runtime = "nodejs";

const AGENT_URL = process.env.AGENT_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  const { message, sessionId } = await req.json();

  const upstream = await fetch(`${AGENT_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(`Agent service error (${upstream.status})`, {
      status: 502,
    });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
