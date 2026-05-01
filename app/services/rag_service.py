from app.core.config import settings


def retrieve_related_context(contract_text: str, top_k: int = 3) -> list[str]:
    """ChromaDB 연동 전 임시 스텁.

    TODO:
    - chromadb.PersistentClient(path=settings.chroma_persist_dir)
    - 컬렉션 로드(settings.chroma_collection)
    - contract_text 임베딩 후 top_k 검색
    """
    _ = (contract_text, top_k, settings.chroma_collection)
    return []
