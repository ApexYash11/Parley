import os
import asyncio
import numpy as np
from dotenv import load_dotenv

load_dotenv()

STT_PROVIDER = os.getenv("STT_PROVIDER", "whisper")


async def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    if STT_PROVIDER == "deepgram":
        from stt.deepgram_stream import send_audio

        return await send_audio(audio, sample_rate)
    else:
        from stt.whisper_local import transcribe as whisper_transcribe

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, whisper_transcribe, audio, sample_rate)
