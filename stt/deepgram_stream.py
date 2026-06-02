import asyncio
import numpy as np
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import os


async def transcribe_chunk(audio: np.ndarray, sample_rate: int = 16000) -> str:
    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY not set")

    client = DeepgramClient(api_key)
    result_text = []

    connection = client.listen.asyncwebsocket.v("1")

    async def on_message(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            result_text.append(transcript)

    connection.on(LiveTranscriptionEvents.Transcript, on_message)

    options = LiveOptions(
        model="nova-2",
        language="en-US",
        smart_format=True,
        sample_rate=sample_rate,
        channels=1,
        encoding="linear16",
    )

    await connection.start(options)
    audio_bytes = (audio.flatten() * 32768).astype("int16").tobytes()
    await connection.send(audio_bytes)
    await asyncio.sleep(1.5)
    await connection.finish()

    return " ".join(result_text)
