# Parley — Real-Time Negotiation Copilot

## Overview

Parley is a real-time negotiation intelligence engine that listens to sales calls via virtual audio, detects high-signal negotiation moments (keywords, entities, semantic triggers), queries knowledge base, LLM-generates contextual signals, and pushes silent visual alerts to a browser overlay on a second screen.

## Architecture

```
Virtual Audio Cable (VB-Cable)
       │
       ▼
┌──────────────┐
│ audio/       │ sounddevice — 16kHz mono float32 chunks every 1.5s
│ capture.py   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ stt/         │ Speech-to-text via Whisper (local) or Deepgram Nova-2 (cloud)
│ router.py    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ trigger/     │ Keyword matching (spaCy) + future semantic matching
│ detector.py  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ knowledge/   │ Policy rules + past deal summaries in ChromaDB vector store
│ store.py     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ llm/         │ OpenRouter client with Gemini→Groq fallback chain
│ client.py    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ server/      │ FastAPI + WebSocket — broadcasts Signal JSON to overlay
│ main.py      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ overlay/     │ HTML/CSS/JS — silent visual alert cards on second screen
│ index.html   │
└──────────────┘
```

## Data Flow

1. **Audio Capture**: `audio/capture.py` uses `sounddevice.InputStream` to capture 1.5s chunks of 16kHz mono audio from VB-Cable virtual audio device
2. **Speech-to-Text**: `stt/router.py` dispatches to either:
   - `stt/whisper_local.py` — faster-whisper (local, free, ~2-3s latency)
   - `stt/deepgram_stream.py` — Deepgram Nova-2 (cloud, ~0.5s latency, requires API key)
3. **Trigger Detection**: `trigger/detector.py` runs keyword/phrase matching using `trigger/keywords.py` patterns across 8 negotiation categories
4. **Knowledge Retrieval**: `knowledge/store.py` queries ChromaDB vector store containing policy rules and past deal summaries
5. **Signal Generation**: `llm/client.py` sends trigger context + knowledge to OpenRouter LLM chain (Gemini Flash → Groq Llama 70B → Groq Llama 8B) and receives a JSON signal
6. **Broadcast**: `server/main.py` sends the Signal JSON to all connected WebSocket clients
7. **Overlay**: `overlay/app.js` renders signal cards (max 6 visible) with type badges, body text, suggested response, evidence source, and a copy button

## Module Reference

### `audio/capture.py`
- `SAMPLE_RATE`: 16000
- `CHUNK_DURATION`: 1.5 seconds
- Functions: `list_devices()`, `find_device_index(name)`, `start_capture(device_name)`, `get_audio_chunk()`

### `stt/whisper_local.py`
- Uses `faster-whisper` with model size "base", CPU, int8 compute
- Lazy-loads model singleton on first call

### `stt/deepgram_stream.py`
- Uses `deepgram-sdk` async WebSocket v1
- Converts float32 audio to int16 linear16 before sending
- Waits 1.5s for response

### `stt/router.py`
- Reads `STT_PROVIDER` from env
- Defaults to "whisper" if not set

### `trigger/keywords.py`
8 trigger categories with hardcoded phrase lists:
- `payment_terms` — net 15/30/45/60, payment terms, invoice, billing cycle
- `pricing` — price, cost, rate, fee, discount, budget, quote
- `liability` — liability, indemnification, damages, cap, exposure
- `ip` — intellectual property, ip ownership, work for hire, license
- `termination` — termination, cancel, exit clause, breach
- `sla` — uptime, sla, response time, availability, support tier
- `exclusivity` — exclusive, exclusivity, non-compete, sole provider
- `renewal` — auto-renew, renewal, evergreen, end of term

### `trigger/detector.py`
- `TriggerEvent` dataclass: category, matched_phrase, full_text, confidence
- `detect(transcript)` → list of TriggerEvent

### `knowledge/store.py`
- ChromaDB in-memory client
- Loads `deals.json` (5 deals) and `policy.json` (5 policy sections) as documents
- `search(query, n=3)` → top-n matching documents

### `knowledge/policy.json`
Pricing floors, payment terms, liability caps, IP defaults, SLA minimums.

### `knowledge/deals.json`
5 example past deals with outcome, notes, and negotiation details.

### `llm/client.py`
- Calls OpenRouter API with `httpx.AsyncClient`
- Model fallback chain: Gemini Flash → Groq Llama 70B → Groq Llama 8B
- 10-second timeout per model

### `llm/prompts.py`
- `SYSTEM_PROMPT`: instructs LLM to return clean JSON only
- `build_user_prompt(trigger_text, context_docs)`: formats the user message

### `server/models.py`
Pydantic models:
- `Signal`: type (risk/policy/suggest/benchmark/clause), title, body, suggested_response, evidence
- `TriggerPayload`: category, matched_phrase, full_text

### `server/main.py`
- FastAPI app on configurable host/port
- WebSocket endpoint `/ws` for overlay clients
- Root `/` serves overlay index.html
- Background asyncio pipeline loop runs continuously

### Overlay
- `index.html`: Base HTML with header (live dot + status) and feed container
- `style.css`: Dark theme, animated card slides, color-coded badges (5 types), copy button
- `app.js`: WebSocket auto-reconnect client, renders up to 6 signal cards, clipboard copy

## Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `STT_PROVIDER` | `whisper` | `whisper` or `deepgram` |
| `DEEPGRAM_API_KEY` | — | Deepgram API key |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `LLM_PRIMARY` | `google/gemini-flash-1.5` | First LLM choice |
| `LLM_FALLBACK_1` | `groq/llama-3.1-70b-versatile` | First fallback |
| `LLM_FALLBACK_2` | `groq/llama-3.1-8b-instant` | Second fallback |
| `AUDIO_DEVICE_NAME` | `CABLE Output (VB-Audio Virtual Cable)` | VB-Cable device name |
| `HOST` | `localhost` | Server host |
| `PORT` | `8765` | Server port |

## Signal Types

| Type | Color | Use Case |
|---|---|---|
| `risk` | Red | Potentially unfavorable term being discussed |
| `policy` | Amber | Term conflicts with company policy |
| `suggest` | Green | Suggested response the rep can say |
| `benchmark` | Blue | Market data / past deal comparison |
| `clause` | Purple | Specific contract clause language |

## Running

1. Install VB-Cable, set as Windows audio output
2. Route Zoom/Meet/Teams call audio through VB-Cable
3. Copy `.env.example` → `.env`, fill API keys
4. `uv run python audio/list_devices.py` to confirm device name
5. `uv run uvicorn server.main:app --host localhost --port 8765 --reload`
6. Open `http://localhost:8765` on second monitor
7. Start call — say "we need Net 15 payment terms" → first card within ~5s (Whisper) or ~2s (Deepgram)

## Dependencies

- `fastapi`, `uvicorn[standard]`, `websockets` — server
- `sounddevice`, `numpy`, `scipy` — audio capture
- `faster-whisper` — local STT
- `deepgram-sdk` — cloud STT
- `spacy` (en_core_web_sm), `sentence-transformers` — trigger detection
- `chromadb` — vector store
- `openai`, `httpx` — LLM client
- `pydantic` — data models
- `python-dotenv` — env management

## Limitations & Future Work

- **Trigger detection**: Currently keyword-only. `embeddings.py` (sentence-transformers) is stubbed for future semantic matching
- **Knowledge base**: In-memory ChromaDB. Could be persisted or swapped for external vector DB
- **Audio**: Single-threaded polling via `queue.Queue`. Could use async audio for lower latency
- **STT**: Whisper local is CPU-only; Deepgram requires API key. No streaming STT pipeline yet — chunks are independent
- **LLM**: Each trigger calls the LLM separately. Could batch or use streaming responses
- **Overlay**: No sound/vibration alerts, no persistent history beyond 6 cards
