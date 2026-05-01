import re

from app.core.config import settings
from app.schemas.contract import AnalyzeResponse, RiskClause
from app.services.llm_service import generate_risk_summary
from app.services.rag_service import retrieve_related_context

RISK_KEYWORDS = {
    "수당": "수당 지급 기준이 불명확하거나 누락될 가능성이 있습니다.",
    "퇴사": "퇴사 조건/절차가 근로자에게 불리할 수 있습니다.",
    "손해배상": "과도한 손해배상 책임이 설정되었을 가능성이 있습니다.",
    "연장근로": "연장근로 수당/동의 절차가 불명확할 수 있습니다.",
    "최저임금": "최저임금 관련 조항 위반 위험이 있을 수 있습니다.",
}


def split_sentences(text: str) -> list[str]:
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", text.strip())
    return [sentence.strip() for sentence in raw_sentences if sentence.strip()]


def analyze_contract_text(text: str) -> AnalyzeResponse:
    sentences = split_sentences(text)
    context_chunks = retrieve_related_context(text, top_k=3)

    risk_clauses: list[RiskClause] = []
    for sentence in sentences:
        for keyword, reason in RISK_KEYWORDS.items():
            if keyword in sentence:
                risk_clauses.append(
                    RiskClause(
                        sentence=sentence,
                        keyword=keyword,
                        reason=reason,
                        evidence=context_chunks,
                    )
                )
                break

    summary = generate_risk_summary(
        risk_count=len(risk_clauses),
        total_sentences=len(sentences),
        context_chunks=context_chunks,
    )

    return AnalyzeResponse(
        total_sentences=len(sentences),
        risk_count=len(risk_clauses),
        risk_clauses=risk_clauses,
        summary=summary,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
    )
