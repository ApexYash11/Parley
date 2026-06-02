# Parley — real-time negotiation copilot

## Setup

1. Install [VB-Cable](https://vb-audio.com/Cable/) and set it as your audio output in Windows sound settings
2. In your Zoom/Meet/Teams call, route audio through VB-Cable
3. Copy `.env.example` to `.env` and fill in your API keys
4. Run: `uv run python audio/list_devices.py` to find your VB-Cable device name
5. Set `AUDIO_DEVICE_NAME` in `.env` to match

## Run

```bash
uv run uvicorn server.main:app --host localhost --port 8765 --reload
```

Open `http://localhost:8765/overlay/index.html` on your second monitor.

## Switch STT

- Whisper (default, free): `STT_PROVIDER=whisper` in `.env`
- Deepgram (faster):       `STT_PROVIDER=deepgram` in `.env`

## Get API keys

- OpenRouter (free): https://openrouter.ai
- Deepgram (free $200 credit): https://deepgram.com
