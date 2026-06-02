from dataclasses import dataclass
from trigger.keywords import detect_keywords


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
    for h in hits:
        events.append(
            TriggerEvent(
                category=h["category"],
                matched_phrase=h["matched"],
                full_text=h["text"],
                confidence=0.9,
            )
        )
    return events
