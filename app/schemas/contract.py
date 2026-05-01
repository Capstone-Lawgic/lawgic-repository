from pydantic import BaseModel, Field


class ContractAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="분석할 계약서 전체 텍스트")


class RiskClause(BaseModel):
    sentence: str
    keyword: str
    reason: str
    evidence: list[str] = []


class AnalyzeResponse(BaseModel):
    total_sentences: int
    risk_count: int
    risk_clauses: list[RiskClause]
    summary: str
    llm_provider: str
    llm_model: str
