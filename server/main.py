import asyncio
import json
import os
import threading
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

app = FastAPI(title="Parley")
app.mount("/overlay", StaticFiles(directory="overlay"), name="overlay")

connected_clients: list[WebSocket] = []


@app.get("/")
async def root():
    return FileResponse("overlay/index.html")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    print(f"[ws] Client connected. Total: {len(connected_clients)}")
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(ws)
        print(f"[ws] Client disconnected. Total: {len(connected_clients)}")


async def broadcast(signal: dict):
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(signal)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


async def pipeline_loop():
    audio_device = os.getenv("AUDIO_DEVICE_NAME")
    stream = start_capture(audio_device)
    print("[parley] Pipeline running. Listening for triggers...")

    loop = asyncio.get_event_loop()

    while True:
        chunk = await loop.run_in_executor(None, get_audio_chunk)
        if chunk is None:
            continue

        transcript = await loop.run_in_executor(None, transcribe, chunk, SAMPLE_RATE)
        if not transcript.strip():
            continue

        print(f"[stt] {transcript}")

        events = detect(transcript)
        if not events:
            continue

        for event in events:
            print(f"[trigger] {event.category} — '{event.matched_phrase}'")
            docs = search(f"{event.category} {event.matched_phrase}")
            user_prompt = build_user_prompt(event.full_text, docs)
            raw = await complete(SYSTEM_PROMPT, user_prompt)

            try:
                signal = json.loads(raw)
                await broadcast(signal)
                print(f"[signal] {signal.get('title', '?')}")
            except json.JSONDecodeError:
                print(f"[llm] Bad JSON: {raw[:100]}")


@app.on_event("startup")
async def startup():
    asyncio.create_task(pipeline_loop())
