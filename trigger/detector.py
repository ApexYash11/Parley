import time
from dataclasses import dataclass
from trigger.keywords import detect_keywords

_last_fired: dict[str, float] = {}
COOLDOWN_SECONDS = 60


@dataclass
class TriggerEvent:
    category: str
    matched_phrase: str
    full_text: str
    confidence: float


def detect(transcript: str) -> list[TriggerEvent]:
    if not transcript.strip():
        return []

    hits = detect_keywords(transcript)
    events = []
    now = time.time()

    for h in hits:
        key = h["matched"]
        last = _last_fired.get(key, 0)
        if now - last < COOLDOWN_SECONDS:
            continue
        _last_fired[key] = now
        events.append(
            TriggerEvent(
                category=h["category"],
                matched_phrase=h["matched"],
                full_text=h["text"],
                confidence=0.9,
            )
        )
    return events
