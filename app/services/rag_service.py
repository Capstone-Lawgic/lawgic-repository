import hashlib
import json
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import chromadb
from chromadb.errors import NotFoundError

from app.core.env import load_environment
from app.schemas.contract import RetrievedContext

load_environment()

APP_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = APP_DIR / "data" / "labor_law_contexts.json"
CHROMA_PATH = APP_DIR / "data" / "chroma"
COLLECTION_NAME = "labor_law_contexts"
EMBEDDING_DIM = 384
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[0-9A-Za-z가-힣]+", text.lower())


def _embed_text_locally(text: str) -> list[float]:
    """Create a deterministic local embedding so Chroma can run without network calls."""
    vector = [0.0] * EMBEDDING_DIM
    tokens = _tokenize(text)

    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector

    return [value / norm for value in vector]


def _embed_text(text: str) -> list[float]:
    """Use OpenAI embeddings when configured, otherwise fall back to local embeddings."""
    if not os.getenv("OPENAI_API_KEY"):
        return _embed_text_locally(text)

    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    except Exception:
        return _embed_text_locally(text)


@lru_cache
def _load_contexts() -> list[dict[str, Any]]:
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def _context_document(item: dict[str, Any]) -> str:
    keywords = ", ".join(item.get("keywords", []))
    return f"{item['title']}\n{item['content']}\n키워드: {keywords}"


def _keyword_score(query: str, metadata: dict[str, Any]) -> float:
    query_tokens = set(_tokenize(query))
    document_tokens = set(
        _tokenize(
            " ".join(
                [
                    str(metadata.get("title", "")),
                    str(metadata.get("content", "")),
                    str(metadata.get("keywords", "")),
                ]
            )
        )
    )

    if not query_tokens:
        return 0.0

    return len(query_tokens & document_tokens) / len(query_tokens)


@lru_cache
def _get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    try:
        client.delete_collection(COLLECTION_NAME)
    except (NotFoundError, ValueError):
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    contexts = _load_contexts()

    if contexts:
        documents = [_context_document(item) for item in contexts]
        collection.add(
            ids=[f"context-{idx}" for idx in range(len(contexts))],
            documents=documents,
            embeddings=[_embed_text(document) for document in documents],
            metadatas=[
                {
                    "source": item["source"],
                    "title": item["title"],
                    "content": item["content"],
                    "keywords": ", ".join(item.get("keywords", [])),
                }
                for item in contexts
            ],
        )

    return collection


def _distance_to_score(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return round(max(0.0, 1.0 - distance), 4)


def retrieve_related_context(contract_text: str, top_k: int = 4) -> list[RetrievedContext]:
    """Retrieve legal review contexts from a local ChromaDB vector collection."""
    if not contract_text.strip() or top_k <= 0:
        return []

    collection = _get_collection()
    collection_count = collection.count()
    if collection_count == 0:
        return []

    n_results = min(collection_count, max(top_k * 4, top_k))
    result = collection.query(
        query_embeddings=[_embed_text(contract_text)],
        n_results=n_results,
        include=["metadatas", "distances"],
    )

    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    contexts_with_score: list[RetrievedContext] = []

    for metadata, distance in zip(metadatas, distances):
        if not metadata:
            continue

        vector_score = _distance_to_score(distance)
        reranked_score = round(vector_score + _keyword_score(contract_text, metadata), 4)
        contexts_with_score.append(
            RetrievedContext(
                source=str(metadata["source"]),
                title=str(metadata["title"]),
                content=str(metadata["content"]),
                score=reranked_score,
            )
        )

    return sorted(contexts_with_score, key=lambda context: context.score, reverse=True)[:top_k]
