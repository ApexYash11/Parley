import sounddevice as sd
import numpy as np
import queue
import os

SAMPLE_RATE = 16000
CHUNK_DURATION = 1.5
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

audio_queue: queue.Queue = queue.Queue()


def list_devices():
    print(sd.query_devices())


def find_device_index(name: str) -> int | None:
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if name.lower() in d["name"].lower() and d["max_input_channels"] > 0:
            return i
    return None


def start_capture(device_name: str | None = None):
    device_index = None
    if device_name:
        device_index = find_device_index(device_name)
        if device_index is None:
            print(f"[audio] Device '{device_name}' not found, using default input")

    def callback(indata, frames, time, status):
        if status:
            print(f"[audio] {status}")
        audio_queue.put(indata.copy())

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK_SAMPLES,
        device=device_index,
        callback=callback,
    )
    stream.start()
    print(
        f"[audio] Capturing from: {sd.query_devices(device_index)['name'] if device_index else 'default'}"
    )
    return stream


def get_audio_chunk() -> np.ndarray | None:
    try:
        return audio_queue.get(timeout=5.0)
    except queue.Empty:
        return None
