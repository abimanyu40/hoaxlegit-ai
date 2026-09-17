import json
import math
from pathlib import Path

import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"  # jalankan: ollama pull nomic-embed-text

DATA_PATH = Path(__file__).parent.parent / "data" / "known_hoaxes.json"
CACHE_PATH = Path(__file__).parent.parent / "data" / "known_hoaxes_embeddings.json"


def _get_embedding(text: str) -> list:
    response = requests.post(OLLAMA_EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return response.json()["embedding"]


def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_index(force: bool = False):
    """Precompute embeddings untuk semua entri di known_hoaxes.json, cache ke file."""
    if CACHE_PATH.exists() and not force:
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    for entry in entries:
        entry["embedding"] = _get_embedding(entry["claim"])

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False)


def search(query: str, top_k: int = 3, min_similarity: float = 0.6) -> list:
    """Cari entri hoax lama yang mirip dengan klaim baru."""
    build_index()

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        entries = json.load(f)

    if not entries:
        return []

    query_embedding = _get_embedding(query)

    scored = []
    for entry in entries:
        sim = _cosine_similarity(query_embedding, entry["embedding"])
        if sim >= min_similarity:
            scored.append({
                "claim": entry["claim"],
                "verdict": entry["verdict"],
                "explanation": entry["explanation"],
                "similarity": round(sim, 3)
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]
