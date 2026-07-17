import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_vectorizer = None
_doc_vectors = None
_documents: list[str] = []


def _load_documents() -> list[str]:
    deals_path = Path(__file__).parent / "deals.json"
    policy_path = Path(__file__).parent / "policy.json"
    docs = []

    with open(deals_path) as f:
        deals = json.load(f)
    for deal in deals:
        docs.append(
            f"Vendor: {deal['vendor']}. Type: {deal['type']}. "
            f"Value: ${deal['value']}. Payment: {deal['payment_terms']}. "
            f"Liability: {deal['liability_cap']}. Discount: {deal['discount']}. "
            f"Outcome: {deal['outcome']}. Notes: {deal['notes']}"
        )

    with open(policy_path) as f:
        policy = json.load(f)
    for key, val in policy.items():
        docs.append(f"Policy — {key}: {json.dumps(val)}")

    return docs


def _ensure_index():
    global _vectorizer, _doc_vectors, _documents
    if _vectorizer is not None:
        return
    _documents = _load_documents()
    _vectorizer = TfidfVectorizer(stop_words="english")
    _doc_vectors = _vectorizer.fit_transform(_documents)


def search(query: str, n: int = 3) -> list[str]:
    _ensure_index()
    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _doc_vectors)[0]
    top_indices = scores.argsort()[-n:][::-1]
    return [_documents[i] for i in top_indices if scores[i] > 0]
