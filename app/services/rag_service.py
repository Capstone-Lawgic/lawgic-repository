import hashlib
import json
import math
import os
import re
import time
from functools import lru_cache
from logging import getLogger
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
logger = getLogger("uvicorn.error")


def _embedding_provider() -> str:
    return "openai" if os.getenv("OPENAI_API_KEY") else "local"


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

        start = time.perf_counter()
        client = OpenAI()
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        logger.info(
            "analysis timing: openai_embedding=%.3fs text_chars=%s",
            time.perf_counter() - start,
            len(text),
        )
        return response.data[0].embedding
    except Exception:
        logger.exception("OpenAI embedding failed; using local embedding fallback")
        return _embed_text_locally(text)


def _embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in one OpenAI request when possible."""
    if not os.getenv("OPENAI_API_KEY"):
        return [_embed_text_locally(text) for text in texts]

    try:
        from openai import OpenAI

        start = time.perf_counter()
        client = OpenAI()
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        logger.info(
            "analysis timing: openai_embeddings_batch=%.3fs text_count=%s",
            time.perf_counter() - start,
            len(texts),
        )
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
    except Exception:
        logger.exception("OpenAI embeddings batch failed; using local embedding fallback")
        return [_embed_text_locally(text) for text in texts]


@lru_cache
def _load_contexts() -> list[dict[str, Any]]:
    with DATA_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def _context_document(item: dict[str, Any]) -> str:
    keywords = ", ".join(item.get("keywords", []))
    return f"{item['title']}\n{item['content']}\n키워드: {keywords}"


def _contexts_hash(contexts: list[dict[str, Any]]) -> str:
    payload = json.dumps(contexts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _collection_metadata(contexts: list[dict[str, Any]]) -> dict[str, str | int]:
    return {
        "hnsw:space": "cosine",
        "embedding_provider": _embedding_provider(),
        "embedding_model": EMBEDDING_MODEL if os.getenv("OPENAI_API_KEY") else "local-hash",
        "context_count": len(contexts),
        "contexts_hash": _contexts_hash(contexts),
    }


def _collection_is_current(collection: Any, contexts: list[dict[str, Any]]) -> bool:
    metadata = collection.metadata or {}
    expected = _collection_metadata(contexts)
    return (
        collection.count() == len(contexts)
        and metadata.get("embedding_provider") == expected["embedding_provider"]
        and metadata.get("embedding_model") == expected["embedding_model"]
        and metadata.get("context_count") == expected["context_count"]
        and metadata.get("contexts_hash") == expected["contexts_hash"]
    )


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
    start = time.perf_counter()
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    logger.info("analysis timing: chroma_client=%.3fs", time.perf_counter() - start)

    start = time.perf_counter()
    contexts = _load_contexts()
    logger.info(
        "analysis timing: load_contexts=%.3fs context_count=%s",
        time.perf_counter() - start,
        len(contexts),
    )

    try:
        start = time.perf_counter()
        collection = client.get_collection(COLLECTION_NAME)
        logger.info("analysis timing: chroma_get_collection=%.3fs", time.perf_counter() - start)
        if _collection_is_current(collection, contexts):
            logger.info("analysis timing: chroma_reuse_collection=True")
            return collection

        start = time.perf_counter()
        client.delete_collection(COLLECTION_NAME)
        logger.info("analysis timing: chroma_delete_collection=%.3fs", time.perf_counter() - start)
    except (NotFoundError, ValueError):
        pass

    start = time.perf_counter()
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata=_collection_metadata(contexts),
    )
    logger.info("analysis timing: chroma_create_collection=%.3fs", time.perf_counter() - start)

    if contexts:
        start = time.perf_counter()
        documents = [_context_document(item) for item in contexts]
        embeddings = _embed_texts(documents)
        logger.info(
            "analysis timing: build_context_embeddings=%.3fs document_count=%s",
            time.perf_counter() - start,
            len(documents),
        )

        start = time.perf_counter()
        collection.add(
            ids=[f"context-{idx}" for idx in range(len(contexts))],
            documents=documents,
            embeddings=embeddings,
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
        logger.info("analysis timing: chroma_add_contexts=%.3fs", time.perf_counter() - start)

    return collection


def _distance_to_score(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return round(max(0.0, 1.0 - distance), 4)


def retrieve_related_context(contract_text: str, top_k: int = 4) -> list[RetrievedContext]:
    """Retrieve legal review contexts from a local ChromaDB vector collection."""
    if not contract_text.strip() or top_k <= 0:
        return []

    start = time.perf_counter()
    collection = _get_collection()
    logger.info("analysis timing: get_collection=%.3fs", time.perf_counter() - start)

    start = time.perf_counter()
    collection_count = collection.count()
    logger.info(
        "analysis timing: chroma_count=%.3fs collection_count=%s",
        time.perf_counter() - start,
        collection_count,
    )
    if collection_count == 0:
        return []

    n_results = min(collection_count, max(top_k * 4, top_k))
    start = time.perf_counter()
    query_embedding = _embed_text(contract_text)
    logger.info(
        "analysis timing: query_embedding=%.3fs text_chars=%s",
        time.perf_counter() - start,
        len(contract_text),
    )

    start = time.perf_counter()
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["metadatas", "distances"],
    )
    logger.info(
        "analysis timing: chroma_query=%.3fs n_results=%s",
        time.perf_counter() - start,
        n_results,
    )

    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    contexts_with_score: list[RetrievedContext] = []

    start = time.perf_counter()
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

    logger.info(
        "analysis timing: rerank_contexts=%.3fs candidate_count=%s",
        time.perf_counter() - start,
        len(contexts_with_score),
    )
    return sorted(contexts_with_score, key=lambda context: context.score, reverse=True)[:top_k]
