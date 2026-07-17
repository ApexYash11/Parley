import asyncio
import json
import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from audio.capture import start_capture, get_audio_chunk, SAMPLE_RATE
from stt.router import transcribe
from trigger.detector import detect
from knowledge.store import search
from llm.client import complete
from llm.prompts import SYSTEM_PROMPT, build_user_prompt
from server.models import Signal

app = FastAPI(title="Parley")
app.mount("/overlay", StaticFiles(directory="overlay"), name="overlay")


# --- 3a: Rolling transcript buffer ---
class RollingBuffer:
    def __init__(self, window_seconds: float = 45.0):
        self.window = window_seconds
        self.entries: list[tuple[float, str]] = []

    def add(self, text: str):
        now = time.time()
        self.entries.append((now, text))
        cutoff = now - self.window
        self.entries = [(t, txt) for t, txt in self.entries if t >= cutoff]

    def get_context(self) -> str:
        cutoff = time.time() - self.window
        return " ".join(txt for t, txt in self.entries if t >= cutoff)


transcript_buffer = RollingBuffer()

# --- 3b: Debounce/coalesce state ---
pending_events: list = []
pending_lock = asyncio.Lock()
debounce_task: asyncio.Task | None = None

# --- 3c: Client list with lock ---
clients_lock = asyncio.Lock()
connected_clients: list[WebSocket] = []


@app.get("/")
async def root():
    return FileResponse("overlay/index.html")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    async with clients_lock:
        connected_clients.append(ws)
        print(f"[ws] Client connected. Total: {len(connected_clients)}")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        async with clients_lock:
            if ws in connected_clients:
                connected_clients.remove(ws)
                print(f"[ws] Client disconnected. Total: {len(connected_clients)}")


async def broadcast(signal: dict):
    dead = []
    async with clients_lock:
        clients_snapshot = connected_clients.copy()
    for ws in clients_snapshot:
        try:
            await ws.send_json(signal)
        except Exception:
            dead.append(ws)
    if dead:
        async with clients_lock:
            for ws in dead:
                if ws in connected_clients:
                    connected_clients.remove(ws)


# --- 3d: Validate Signal before broadcasting ---
async def validate_and_broadcast(raw: str):
    try:
        parsed = json.loads(raw)
        signal = Signal(**parsed)
        await broadcast(signal.model_dump())
        print(f"[signal] {signal.title}")
    except (json.JSONDecodeError, Exception) as e:
        print(f"[llm] Validation failed: {e} — attempting repair")
        repair_prompt = f"""The following was supposed to be valid JSON but failed validation.
Fix it to match this EXACT schema and return ONLY the corrected JSON, no markdown, no preamble:

- type: must be exactly one of these five strings — "risk", "policy", "suggest", "benchmark", "clause"
- title: string, max 7 words
- body: string, one sentence
- suggested_response: string, or null if not applicable
- evidence: string

Broken output to fix:
{raw}"""
        repaired = await complete(SYSTEM_PROMPT, repair_prompt)
        try:
            parsed = json.loads(repaired)
            signal = Signal(**parsed)
            await broadcast(signal.model_dump())
            print(f"[signal] {signal.title} (after repair)")
        except Exception as e2:
            print(f"[llm] Repair also failed: {e2} — dropping signal")


# --- 3b: Debounce and coalesce ---
async def schedule_debounced_flush():
    global debounce_task
    if debounce_task and not debounce_task.done():
        return
    debounce_task = asyncio.create_task(flush_after_debounce())


async def flush_after_debounce():
    await asyncio.sleep(0.8)
    async with pending_lock:
        events_to_process = pending_events.copy()
        pending_events.clear()
    if events_to_process:
        await process_batch(events_to_process)


async def process_batch(events: list):
    context = transcript_buffer.get_context()
    all_docs = []
    for event in events:
        docs = search(f"{event.category} {event.matched_phrase}")
        all_docs.extend(docs)
    combined_text = " | ".join(e.full_text for e in events)
    user_prompt = build_user_prompt(combined_text, list(set(all_docs)))
    raw = await complete(SYSTEM_PROMPT, user_prompt)
    await validate_and_broadcast(raw)

    async with pending_lock:
        more_events_arrived = len(pending_events) > 0
    if more_events_arrived:
        asyncio.create_task(flush_after_debounce())


async def pipeline_loop():
    audio_device = os.getenv("AUDIO_DEVICE_NAME")
    stream = start_capture(audio_device)
    print("[parley] Pipeline running. Listening for triggers...")

    loop = asyncio.get_event_loop()

    while True:
        chunk = await loop.run_in_executor(None, get_audio_chunk)
        if chunk is None:
            continue

        transcript = await transcribe(chunk, SAMPLE_RATE)
        if not transcript.strip():
            continue

        print(f"[stt] {transcript}")
        transcript_buffer.add(transcript)

        events = detect(transcript)
        if events:
            async with pending_lock:
                pending_events.extend(events)
            await schedule_debounced_flush()


@app.on_event("startup")
async def startup():
    asyncio.create_task(pipeline_loop())
