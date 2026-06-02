import json
import chromadb
from pathlib import Path

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    _client = chromadb.Client()
    _collection = _client.get_or_create_collection("parley_knowledge")

    deals_path = Path(__file__).parent / "deals.json"
    policy_path = Path(__file__).parent / "policy.json"

    with open(deals_path) as f:
        deals = json.load(f)

    for deal in deals:
        text = (
            f"Vendor: {deal['vendor']}. Type: {deal['type']}. "
            f"Value: ${deal['value']}. Payment: {deal['payment_terms']}. "
            f"Liability: {deal['liability_cap']}. Discount: {deal['discount']}. "
            f"Outcome: {deal['outcome']}. Notes: {deal['notes']}"
        )
        _collection.upsert(documents=[text], ids=[deal["id"]])

    with open(policy_path) as f:
        policy = json.load(f)

    for key, val in policy.items():
        _collection.upsert(
            documents=[f"Policy — {key}: {json.dumps(val)}"], ids=[f"policy_{key}"]
        )

    return _collection


def search(query: str, n: int = 3) -> list[str]:
    col = get_collection()
    results = col.query(query_texts=[query], n_results=n)
    return results["documents"][0] if results["documents"] else []
