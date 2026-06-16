from pydantic import BaseModel, ConfigDict, Field

from app.core.contract_domain import ContractDomain


class ContractAnalyzeRequest(BaseModel):
    text: str = Field(..., description="분석할 계약서 전체 텍스트")
    contract_type: ContractDomain | None = Field(
        default=None,
        description="계약서 유형. 비워두면 텍스트에서 자동 판별합니다.",
    )


class RetrievedContext(BaseModel):
    source: str
    title: str
    content: str
    score: float


class RiskClause(BaseModel):
    sentence: str
    category: str
    severity: str
    reason: str
    evidence: str
    recommendation: str
    related_contexts: list[RetrievedContext] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    contract_type: ContractDomain
    total_sentences: int
    risk_count: int
    risk_clauses: list[RiskClause]
    summary: str
    model_used: str
    contexts: list[RetrievedContext]
