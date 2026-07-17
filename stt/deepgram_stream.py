import asyncio
import numpy as np
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import os

_connection = None
_latest_transcript: list[str] = []


async def get_connection():
    global _connection
    if _connection is not None:
        return _connection

    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not set")

    client = DeepgramClient(api_key)
    _connection = client.listen.asyncwebsocket.v("1")

    def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            _latest_transcript.append(transcript)

    _connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        sample_rate=16000,
        channels=1,
        encoding="linear16",
    )
    await _connection.start(options)
    return _connection


async def send_audio(audio: np.ndarray, sample_rate: int = 16000) -> str:
    conn = await get_connection()
    _latest_transcript.clear()
    audio_bytes = (audio.flatten() * 32768).astype("int16").tobytes()
    await conn.send(audio_bytes)
    await asyncio.sleep(0.3)
    return " ".join(_latest_transcript)
