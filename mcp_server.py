import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastmcp import Client, FastMCP
from prefab_ui import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Column,
    Heading,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.control_flow import ForEach
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rabbit_hole")

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("Rabbit Hole Knowledge Mapper")

GRAPH_FILE = Path(__file__).parent / "knowledge_graph.json"

# SSE clients — one asyncio.Queue per connected browser tab
_sse_clients: list[asyncio.Queue] = []


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class PathStep(BaseModel):
    step: int
    concept: str
    wikipedia_extract: str
    wikipedia_url: str
    connection_to_next: str | None


class RabbitHole(BaseModel):
    id: str
    created_at: str
    concept_a: str
    concept_b: str
    steps: list[PathStep]


class FindPathRequest(BaseModel):
    concept_a: str
    concept_b: str
    nvidia_api_key: str
    steps: int = 4


class ImportRequest(BaseModel):
    entries: list[dict]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_graph() -> list[dict]:
    if not GRAPH_FILE.exists():
        return []
    return json.loads(GRAPH_FILE.read_text())


def _write_graph(data: list[dict]) -> None:
    GRAPH_FILE.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# MCP Tool 1 — fetch Wikipedia context (internet fetch)
# ---------------------------------------------------------------------------
@mcp.tool()
async def fetch_concept_context(concept: str) -> dict:
    """Fetch a Wikipedia article summary for a concept."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{concept.replace(' ', '_')}"
    log.info("[Tool 1] fetch_concept_context → '%s'", concept)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers={"User-Agent": "RabbitHoleMCP/1.0"})
        if resp.status_code == 404:
            log.warning("[Tool 1] Wikipedia 404 for '%s'", concept)
            raise ValueError(f"No Wikipedia article found for '{concept}'")
        resp.raise_for_status()
        data = resp.json()
        result = {
            "title": data.get("title", concept),
            "extract": data.get("extract", ""),
            "thumbnail_url": (data.get("thumbnail") or {}).get("source", ""),
            "page_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
        log.info("[Tool 1] Wikipedia OK — title='%s', extract_len=%d", result["title"], len(result["extract"]))
        return result


# ---------------------------------------------------------------------------
# MCP Tool 2 — CRUD on knowledge_graph.json (local file)
# ---------------------------------------------------------------------------
@mcp.tool()
async def crud_knowledge_graph(action: str, payload: dict | None = None) -> dict:
    """
    CRUD operations on knowledge_graph.json.
    action: 'create' | 'list' | 'delete'
    payload for create: RabbitHole fields (minus id/created_at)
    payload for delete: { "id": "<uuid>" }
    """
    log.info("[Tool 2] crud_knowledge_graph action='%s'", action)
    entries = _read_graph()

    if action == "list":
        log.info("[Tool 2] list → %d entries in graph", len(entries))
        return {"entries": entries, "count": len(entries)}

    if action == "create":
        entry = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            **(payload or {}),
        }
        entries.append(entry)
        _write_graph(entries)
        log.info("[Tool 2] created entry id=%s, graph now has %d entries", entry["id"], len(entries))
        return {"entry": entry}

    if action == "delete":
        entry_id = (payload or {}).get("id")
        before = len(entries)
        entries = [e for e in entries if e.get("id") != entry_id]
        _write_graph(entries)
        log.info("[Tool 2] deleted %d entry(ies) with id=%s", before - len(entries), entry_id)
        return {"deleted": before - len(entries)}

    raise ValueError(f"Unknown action: {action}")


# ---------------------------------------------------------------------------
# MCP Tool 3 — render Prefab UI and stream to browser (UI communication)
# ---------------------------------------------------------------------------
@mcp.tool(app=True)
async def render_rabbit_hole_ui(path_data: dict) -> PrefabApp:
    """
    Render the rabbit hole path as an interactive Prefab UI.
    Also broadcasts the raw data to connected SSE clients (React frontend).
    """
    steps: list[dict] = path_data.get("steps", [])
    concept_a: str = path_data.get("concept_a", "")
    concept_b: str = path_data.get("concept_b", "")
    created_at: str = path_data.get("created_at", "")

    log.info("[Tool 3] render_rabbit_hole_ui — building Prefab UI for '%s' → '%s'", concept_a, concept_b)

    # ── Build Prefab component tree ────────────────────────────────────────
    with Column(gap=6, css_class="p-6 max-w-2xl mx-auto") as view:

        # Header
        with Row(justify="between", align="center", css_class="mb-2"):
            with Column(gap=1):
                Heading(f"{concept_a}  →  {concept_b}", css_class="text-2xl font-bold")
                Text(
                    f"{len(steps)} steps  •  {created_at[:10] if created_at else ''}",
                    css_class="text-sm text-muted-foreground italic",
                )
            Badge(f"🐇 Rabbit Hole", css_class="self-start")

        Separator()

        # One card per step, rendered from state via ForEach
        with ForEach("steps") as step:
            with Card(css_class="border-l-4 border-l-amber-400 shadow-sm"):
                with CardHeader(css_class="pb-2"):
                    with Row(align="center", gap=3):
                        Badge(
                            "{{ step.step }}",
                            variant="outline",
                            css_class="text-xs font-mono",
                        )
                        CardTitle("{{ step.concept }}", css_class="text-lg")
                with CardContent(css_class="pt-0"):
                    Text(
                        "{{ step.wikipedia_extract }}",
                        css_class="text-sm text-muted-foreground italic leading-relaxed",
                    )
                    # Connector annotation (only when connection_to_next exists)
                    Text(
                        "↳ {{ step.connection_to_next }}",
                        css_class="text-xs text-amber-700 mt-3 px-3 py-1.5 bg-amber-50 border border-dashed border-amber-300 rounded-md inline-block",
                    )

    prefab_app = PrefabApp(
        view=view,
        state={"steps": steps},
        title=f"{concept_a} → {concept_b}",
    )

    log.info("[Tool 3] Prefab UI built — %d step cards", len(steps))

    # ── Also push raw data to SSE so React frontend updates live ──────────
    event = {"type": "path_update", "data": path_data}
    for q in _sse_clients:
        await q.put(event)
    log.info("[Tool 3] SSE broadcast to %d client(s)", len(_sse_clients))

    return prefab_app


# ---------------------------------------------------------------------------
# FastAPI app — REST endpoints + MCP server mounted at /mcp
# ---------------------------------------------------------------------------
# Build the MCP HTTP sub-app first so we can borrow its lifespan
mcp_http_app = mcp.http_app(path="/mcp")

app = FastAPI(
    title="Rabbit Hole Knowledge Mapper API",
    lifespan=mcp_http_app.lifespan,   # share FastMCP's lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the real MCP server — accessible to any MCP client at /mcp-server/mcp
app.mount("/mcp-server", mcp_http_app)

log.info("MCP server mounted at http://localhost:8000/mcp-server/mcp")


# ---------------------------------------------------------------------------
# REST endpoints (used by React frontend)
# ---------------------------------------------------------------------------
@app.get("/library")
async def get_library() -> dict:
    return {"entries": _read_graph()}


@app.delete("/library/{entry_id}")
async def delete_entry(entry_id: str) -> dict:
    entries = _read_graph()
    before = len(entries)
    entries = [e for e in entries if e.get("id") != entry_id]
    _write_graph(entries)
    return {"deleted": before - len(entries)}


@app.post("/import")
async def import_library(req: ImportRequest) -> dict:
    _write_graph(req.entries)
    return {"count": len(req.entries)}


@app.get("/events")
async def sse_events(request: Request):
    """SSE stream — React subscribes here via EventSource."""
    q: asyncio.Queue = asyncio.Queue()
    _sse_clients.append(q)
    log.info("[SSE] client connected — total clients: %d", len(_sse_clients))

    async def generator():
        try:
            yield "data: {\"type\": \"connected\"}\n\n"
            while True:
                if await request.is_disconnected():
                    log.info("[SSE] client disconnected")
                    break
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15)
                    log.info("[SSE] sending event type='%s'", event.get("type"))
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield "data: {\"type\": \"ping\"}\n\n"
        finally:
            _sse_clients.remove(q)
            log.info("[SSE] client removed — total clients: %d", len(_sse_clients))

    return StreamingResponse(generator(), media_type="text/event-stream")


@app.post("/find-path")
async def find_path(req: FindPathRequest) -> dict:
    """
    Orchestrator: all three MCP tools are invoked via a real FastMCP Client
    (in-memory MCP protocol — not plain Python calls).
    Flow: Tool 1 (Wikipedia) → NVIDIA NIM → Tool 1 again (enrich steps)
          → Tool 2 (save JSON) → Tool 3 (Prefab UI + SSE)
    """
    log.info("━" * 60)
    log.info("[/find-path] START  '%s'  →  '%s'  (%d steps)", req.concept_a, req.concept_b, req.steps)
    log.info("[/find-path] Opening in-memory MCP client → real MCP protocol for all tool calls")

    async with Client(mcp) as mcp_client:

        # ── Tool 1 (×2): fetch Wikipedia context via MCP ─────────────────
        log.info("[/find-path] [MCP] call_tool → fetch_concept_context('%s')", req.concept_a)
        try:
            result_a = await mcp_client.call_tool(
                "fetch_concept_context", {"concept": req.concept_a}
            )
            ctx_a: dict = result_a.data
            log.info("[/find-path] [MCP] ← fetch_concept_context OK: title='%s'", ctx_a.get("title"))

            log.info("[/find-path] [MCP] call_tool → fetch_concept_context('%s')", req.concept_b)
            result_b = await mcp_client.call_tool(
                "fetch_concept_context", {"concept": req.concept_b}
            )
            ctx_b: dict = result_b.data
            log.info("[/find-path] [MCP] ← fetch_concept_context OK: title='%s'", ctx_b.get("title"))
        except Exception as e:
            log.error("[/find-path] Wikipedia MCP call failed: %s", e)
            raise HTTPException(status_code=422, detail=str(e))

        # ── NVIDIA NIM: reason about the path (not an MCP tool) ──────────
        log.info("[/find-path] Calling NVIDIA NIM API (model=meta/llama-3.1-70b-instruct)")
        system_prompt = (
            "You are a knowledge connector. Given two concepts and their Wikipedia context, "
            f"find exactly {req.steps} semantic steps that connect them. "
            "Return ONLY a valid JSON array with no extra text. "
            f"The array must contain exactly {req.steps} objects. "
            "Each object must have these keys: "
            '"concept" (string), '
            '"wikipedia_search_term" (string — the Wikipedia article title to search), '
            '"wikipedia_extract" (string — one sentence describing this concept), '
            '"connection_to_next" (string or null — how this concept links to the next; null for last step). '
            f'The first object\'s concept must be "{req.concept_a}" and the last must be "{req.concept_b}".'
        )
        user_prompt = (
            f'Connect "{req.concept_a}" to "{req.concept_b}" in exactly {req.steps} steps.\n\n'
            f"Wikipedia context for {req.concept_a}:\n{ctx_a['extract'][:600]}\n\n"
            f"Wikipedia context for {req.concept_b}:\n{ctx_b['extract'][:600]}\n\n"
            f"Return a JSON array of exactly {req.steps} steps."
        )

        async with httpx.AsyncClient(timeout=60) as http:
            nvidia_resp = await http.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {req.nvidia_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "meta/llama-3.1-70b-instruct",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1500,
                },
            )

        if nvidia_resp.status_code != 200:
            log.error("[/find-path] NVIDIA error %d: %s", nvidia_resp.status_code, nvidia_resp.text[:300])
            raise HTTPException(
                status_code=502,
                detail=f"NVIDIA API error {nvidia_resp.status_code}: {nvidia_resp.text[:300]}",
            )

        log.info("[/find-path] NVIDIA responded OK (HTTP 200)")
        raw_content = nvidia_resp.json()["choices"][0]["message"]["content"].strip()
        log.info("[/find-path] Raw NVIDIA output (%d chars):\n%s", len(raw_content), raw_content[:800])

        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
        raw_content = raw_content.strip()

        try:
            steps_raw: list[dict] = json.loads(raw_content)
            log.info("[/find-path] Parsed %d steps from NVIDIA", len(steps_raw))
        except json.JSONDecodeError as e:
            log.error("[/find-path] JSON parse failed: %s\nContent: %s", e, raw_content[:400])
            raise HTTPException(status_code=502, detail="NVIDIA returned malformed JSON.")

        # ── Tool 1 (×N): enrich each step with real Wikipedia data via MCP ─
        log.info("[/find-path] Enriching %d steps via MCP Tool 1 (Wikipedia)...", len(steps_raw))
        enriched_steps: list[dict] = []
        for i, s in enumerate(steps_raw[: req.steps]):
            search_term = s.get("wikipedia_search_term", s["concept"])
            log.info("[/find-path] [MCP] call_tool → fetch_concept_context('%s')", search_term)
            try:
                wiki_result = await mcp_client.call_tool(
                    "fetch_concept_context", {"concept": search_term}
                )
                wiki: dict = wiki_result.data
                wiki_url = wiki["page_url"]
                wiki_extract = wiki["extract"][:300]
                log.info("[/find-path] [MCP] ← OK: '%s'", wiki.get("title"))
            except Exception:
                wiki_url = f"https://en.wikipedia.org/wiki/{s['concept'].replace(' ', '_')}"
                wiki_extract = s.get("wikipedia_extract", "")
                log.warning("[/find-path] [MCP] ← Wikipedia fallback for '%s'", s["concept"])

            enriched_steps.append({
                "step": i + 1,
                "concept": s["concept"],
                "wikipedia_extract": wiki_extract,
                "wikipedia_url": wiki_url,
                "connection_to_next": s.get("connection_to_next"),
            })
            log.info(
                "[/find-path]   step %d: '%s' → %s",
                i + 1, s["concept"], s.get("connection_to_next", "END"),
            )

        # ── Tool 2: save to knowledge_graph.json via MCP ─────────────────
        log.info("[/find-path] [MCP] call_tool → crud_knowledge_graph(action='create')")
        save_result = await mcp_client.call_tool(
            "crud_knowledge_graph",
            {
                "action": "create",
                "payload": {
                    "concept_a": req.concept_a,
                    "concept_b": req.concept_b,
                    "steps": enriched_steps,
                },
            },
        )
        rabbit_hole: dict = save_result.data["entry"]
        log.info("[/find-path] [MCP] ← crud_knowledge_graph OK: id=%s", rabbit_hole["id"])

        # ── Tool 3: render Prefab UI + SSE broadcast via MCP ─────────────
        log.info("[/find-path] [MCP] call_tool → render_rabbit_hole_ui (Prefab + SSE)")
        await mcp_client.call_tool("render_rabbit_hole_ui", {"path_data": rabbit_hole})
        log.info("[/find-path] [MCP] ← render_rabbit_hole_ui OK")

    log.info("[/find-path] DONE — id=%s", rabbit_hole["id"])
    log.info("━" * 60)
    return rabbit_hole


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8000, reload=True)
