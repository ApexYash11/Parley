from faster_whisper import WhisperModel
import numpy as np

_model = None


def load_model(size: str = "base"):
    global _model
    if _model is None:
        print(f"[whisper] Loading model: {size}")
        _model = WhisperModel(size, device="cpu", compute_type="int8")
        print("[whisper] Model ready")
    return _model


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    model = load_model()
    audio_flat = audio.flatten().astype("float32")
    segments, _ = model.transcribe(audio_flat, beam_size=3, language="en")
    return " ".join(s.text.strip() for s in segments)
