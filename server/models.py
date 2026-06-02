from pydantic import BaseModel
from typing import Literal


class Signal(BaseModel):
    type: Literal["risk", "policy", "suggest", "benchmark", "clause"]
    title: str
    body: str
    suggested_response: str | None
    evidence: str


class TriggerPayload(BaseModel):
    category: str
    matched_phrase: str
    full_text: str
