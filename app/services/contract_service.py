import re

from app.schemas.contract import AnalyzeResponse
from app.services.llm_service import analyze_with_llm
from app.services.rag_service import retrieve_related_context


def split_sentences(text: str) -> list[str]:
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", text.strip())
    return [sentence.strip() for sentence in raw_sentences if sentence.strip()]


def analyze_contract_text(text: str) -> AnalyzeResponse:
    sentences = split_sentences(text)
    contexts = retrieve_related_context(text)
    summary, risk_clauses, model_used = analyze_with_llm(
        contract_text=text,
        sentences=sentences,
        contexts=contexts,
    )

    return AnalyzeResponse(
        total_sentences=len(sentences),
        risk_count=len(risk_clauses),
        risk_clauses=risk_clauses,
        summary=summary,
        model_used=model_used,
        contexts=contexts,
    )
