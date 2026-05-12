import os

from pydantic import BaseModel, Field

from app.core.env import load_environment
from app.schemas.contract import RetrievedContext, RiskClause

load_environment()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class LLMRiskClause(BaseModel):
    sentence: str = Field(description="위험하다고 판단한 계약서 원문 문장")
    category: str = Field(description="위험 유형")
    severity: str = Field(description="low, medium, high 중 하나")
    reason: str = Field(description="위험하다고 판단한 이유")
    evidence: str = Field(description="판단에 사용한 RAG 근거 요약")
    recommendation: str = Field(description="계약서 수정 또는 확인 권고")


class LLMAnalyzeResult(BaseModel):
    summary: str
    risk_clauses: list[LLMRiskClause]


RISK_RULES = {
    "수당": ("임금/수당", "medium", "수당 지급 기준이 불명확하거나 누락될 가능성이 있습니다."),
    "퇴사": ("퇴사/위약금", "high", "퇴사 조건이 근로자에게 불리하거나 위약금 성격일 수 있습니다."),
    "손해배상": ("손해배상", "high", "근로자에게 과도한 손해배상 책임을 부과할 수 있습니다."),
    "연장근로": ("근로시간", "medium", "연장근로 동의 절차나 가산수당 지급 기준이 불명확할 수 있습니다."),
    "최저임금": ("임금/최저임금", "high", "최저임금 준수 여부를 확인해야 합니다."),
    "위약금": ("퇴사/위약금", "high", "퇴사나 계약 위반 시 정액 배상을 예정하는 표현은 위험할 수 있습니다."),
    "경업금지": ("경업금지", "medium", "퇴직 후 직업 선택의 자유를 과도하게 제한할 수 있습니다."),
    "개인정보": ("개인정보", "medium", "개인정보 수집ㆍ이용 목적, 보유 기간, 제공 범위가 불명확할 수 있습니다."),
    "제3자": ("개인정보", "medium", "개인정보 제3자 제공은 목적, 제공받는 자, 항목, 보유 기간을 구체화해야 합니다."),
    "동종업계": ("경업금지", "medium", "퇴직 후 취업 제한은 기간, 지역, 대상 업무, 보상 여부가 과도하면 위험할 수 있습니다."),
    "근무 장소": ("근로조건 변경", "medium", "근무 장소나 직무를 일방적으로 바꾸는 조항은 근로조건 변경 위험이 있습니다."),
}


def _contexts_to_prompt(contexts: list[RetrievedContext]) -> str:
    if not contexts:
        return "관련 근거가 검색되지 않았습니다."

    return "\n\n".join(
        f"[{idx}] {context.title}\n출처: {context.source}\n내용: {context.content}"
        for idx, context in enumerate(contexts, start=1)
    )


def _evidence_from_context(context: RetrievedContext | None) -> str:
    if not context:
        return "로컬 규칙 기반으로 탐지했습니다. 관련 RAG 근거는 검색되지 않았습니다."
    return f"{context.title} ({context.source}): {context.content}"


def _fallback_analyze(
    contract_text: str,
    sentences: list[str],
    contexts: list[RetrievedContext],
) -> LLMAnalyzeResult:
    risk_clauses: list[LLMRiskClause] = []

    for sentence in sentences:
        for keyword, (category, severity, reason) in RISK_RULES.items():
            if keyword in sentence:
                related_context = contexts[0] if contexts else None
                risk_clauses.append(
                    LLMRiskClause(
                        sentence=sentence,
                        category=category,
                        severity=severity,
                        reason=reason,
                        evidence=_evidence_from_context(related_context),
                        recommendation="해당 조항의 조건, 절차, 산정 기준을 구체화하고 법적 검토를 받으세요.",
                    )
                )
                break

    if not contract_text.strip():
        summary = "분석할 계약서 내용이 없습니다."
    elif risk_clauses:
        summary = f"총 {len(sentences)}개 문장 중 {len(risk_clauses)}개의 잠재적 위험 조항이 탐지되었습니다."
    else:
        summary = f"총 {len(sentences)}개 문장에서 뚜렷한 위험 조항은 탐지되지 않았습니다."

    return LLMAnalyzeResult(summary=summary, risk_clauses=risk_clauses)


def _build_risk_clause(
    clause: LLMRiskClause,
    contexts: list[RetrievedContext],
) -> RiskClause:
    return RiskClause(
        sentence=clause.sentence,
        category=clause.category,
        severity=clause.severity,
        reason=clause.reason,
        evidence=clause.evidence,
        recommendation=clause.recommendation,
        related_contexts=contexts[:2],
    )


def analyze_with_llm(
    contract_text: str,
    sentences: list[str],
    contexts: list[RetrievedContext],
) -> tuple[str, list[RiskClause], str]:
    """RAG 근거를 바탕으로 LLM 계약서 위험 분석을 수행한다."""
    if not os.getenv("OPENAI_API_KEY"):
        result = _fallback_analyze(contract_text, sentences, contexts)
        return (
            result.summary,
            [_build_risk_clause(clause, contexts) for clause in result.risk_clauses],
            "local-fallback",
        )

    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.responses.parse(
            model=DEFAULT_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "너는 한국 근로계약서 위험 조항 검토 도우미다. "
                        "반드시 제공된 RAG 근거와 계약서 원문에 기반해 판단한다. "
                        "법률 자문이 아니라 검토 보조 결과임을 전제로, 과장하지 말고 구체적으로 작성한다. "
                        "각 위험 조항의 evidence에는 사용한 RAG 근거의 제목과 출처를 포함한다. "
                        "제공된 RAG 근거에 없는 법령명이나 조문은 새로 만들지 않는다. "
                        "근거가 부족하면 단정하지 말고 추가 검토가 필요하다고 쓴다."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "아래 계약서를 검토하고 위험 조항만 추출해 JSON으로 답하라.\n\n"
                        "각 항목은 sentence, category, severity, reason, evidence, recommendation을 채운다. "
                        "evidence에는 반드시 관련 RAG 근거의 제목과 출처를 함께 적는다.\n\n"
                        f"[RAG 근거]\n{_contexts_to_prompt(contexts)}\n\n"
                        f"[계약서]\n{contract_text}"
                    ),
                },
            ],
            text_format=LLMAnalyzeResult,
        )
        result = response.output_parsed
    except Exception:
        result = _fallback_analyze(contract_text, sentences, contexts)
        return (
            f"{result.summary} OpenAI 분석 중 오류가 발생해 로컬 fallback 결과를 표시합니다.",
            [_build_risk_clause(clause, contexts) for clause in result.risk_clauses],
            "local-fallback",
        )

    return (
        result.summary,
        [_build_risk_clause(clause, contexts) for clause in result.risk_clauses],
        DEFAULT_MODEL,
    )


def generate_risk_summary(risk_count: int, total_sentences: int) -> str:
    if risk_count == 0:
        return f"총 {total_sentences}개 문장 중 위험 키워드는 발견되지 않았습니다."

    return f"총 {total_sentences}개 문장 중 {risk_count}개의 잠재적 위험 조항이 탐지되었습니다."
