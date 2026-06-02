import sounddevice as sd

if __name__ == "__main__":
    devices = sd.query_devices()
    print("\nAvailable audio input devices:\n")
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            print(f"  [{i}] {d['name']}")
    print("\nSet AUDIO_DEVICE_NAME in .env to match your VB-Cable device name")
