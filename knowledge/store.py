import json
import os
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

os.environ.pop("HF_TOKEN", None)
os.environ.pop("HUGGINGFACE_HUB_TOKEN", None)

_client = None
_model = None
_collection_name = "parley_knowledge"


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_client():
    global _client
    if _client is not None:
        return _client

    _client = QdrantClient(":memory:")
    col = _client.collection_exists(_collection_name)
    if not col:
        _client.create_collection(
            collection_name=_collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        _populate(_client)
    return _client


def _populate(client):
    model = get_model()
    points = []
    idx = 0

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
        vector = model.encode(text).tolist()
        points.append(
            PointStruct(id=idx, vector=vector, payload={"text": text, "id": deal["id"]})
        )
        idx += 1

    with open(policy_path) as f:
        policy = json.load(f)

    for key, val in policy.items():
        text = f"Policy — {key}: {json.dumps(val)}"
        vector = model.encode(text).tolist()
        points.append(
            PointStruct(
                id=idx, vector=vector, payload={"text": text, "id": f"policy_{key}"}
            )
        )
        idx += 1

    client.upsert(collection_name=_collection_name, points=points)


def search(query: str, n: int = 3) -> list[str]:
    client = get_client()
    model = get_model()
    query_vector = model.encode(query).tolist()
    results = client.query_points(
        collection_name=_collection_name,
        query=query_vector,
        limit=n,
    )
    return [r.payload["text"] for r in results.points]
