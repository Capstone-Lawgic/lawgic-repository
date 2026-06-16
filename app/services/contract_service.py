import re
import time
from logging import getLogger

from app.core.contract_domain import ContractDomain, detect_contract_domain
from app.schemas.contract import AnalyzeResponse
from app.services.llm_service import analyze_with_llm
from app.services.rag_service import retrieve_related_context

logger = getLogger("uvicorn.error")


def split_sentences(text: str) -> list[str]:
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", text.strip())
    return [sentence.strip() for sentence in raw_sentences if sentence.strip()]


def analyze_contract_text(
    text: str,
    contract_type: ContractDomain | None = None,
) -> AnalyzeResponse:
    total_start = time.perf_counter()
    detected_contract_type = contract_type or detect_contract_domain(text)

    step_start = time.perf_counter()
    sentences = split_sentences(text)
    logger.info(
        "analysis timing: split_sentences=%.3fs sentence_count=%s text_chars=%s",
        time.perf_counter() - step_start,
        len(sentences),
        len(text),
    )

    step_start = time.perf_counter()
    contexts = retrieve_related_context(text, contract_type=detected_contract_type)
    logger.info(
        "analysis timing: retrieve_related_context=%.3fs contract_type=%s context_count=%s",
        time.perf_counter() - step_start,
        detected_contract_type,
        len(contexts),
    )

    step_start = time.perf_counter()
    summary, risk_clauses, model_used = analyze_with_llm(
        contract_text=text,
        sentences=sentences,
        contexts=contexts,
        contract_type=detected_contract_type,
    )
    logger.info(
        "analysis timing: analyze_with_llm=%.3fs model=%s risk_count=%s",
        time.perf_counter() - step_start,
        model_used,
        len(risk_clauses),
    )
    logger.info("analysis timing: total=%.3fs", time.perf_counter() - total_start)

    return AnalyzeResponse(
        contract_type=detected_contract_type,
        total_sentences=len(sentences),
        risk_count=len(risk_clauses),
        risk_clauses=risk_clauses,
        summary=summary,
        model_used=model_used,
        contexts=contexts,
    )
