import re

TRIGGER_PATTERNS = {
    "payment_terms": [
        "net 15",
        "net 30",
        "net 45",
        "net 60",
        "payment terms",
        "invoice",
        "billing cycle",
    ],
    "pricing": [
        "price",
        "cost",
        "rate",
        "fee",
        "discount",
        "percentage off",
        "budget",
        "quote",
    ],
    "liability": [
        "liability",
        "indemnification",
        "damages",
        "cap",
        "exposure",
        "responsible for",
    ],
    "ip": [
        "intellectual property",
        "ip ownership",
        "work for hire",
        "license",
        "proprietary",
    ],
    "termination": ["termination", "cancel", "exit clause", "30 days notice", "breach"],
    "sla": ["uptime", "sla", "response time", "availability", "99", "support tier"],
    "exclusivity": ["exclusive", "exclusivity", "non-compete", "sole provider"],
    "renewal": ["auto-renew", "renewal", "evergreen", "end of term"],
}


def detect_keywords(text: str) -> list[dict]:
    text_lower = text.lower()
    hits = []
    for category, patterns in TRIGGER_PATTERNS.items():
        for pattern in patterns:
            if re.search(r"\b" + re.escape(pattern) + r"\b", text_lower):
                hits.append({"category": category, "matched": pattern, "text": text})
                break
    return hits
