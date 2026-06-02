import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()

STT_PROVIDER = os.getenv("STT_PROVIDER", "whisper")


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    if STT_PROVIDER == "deepgram":
        import asyncio
        from stt.deepgram_stream import transcribe_chunk

        return asyncio.run(transcribe_chunk(audio, sample_rate))
    else:
        from stt.whisper_local import transcribe

        return transcribe(audio, sample_rate)
