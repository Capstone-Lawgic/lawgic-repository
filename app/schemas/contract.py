from pydantic import BaseModel, Field


class ContractAnalyzeRequest(BaseModel):
    text: str = Field(..., description="분석할 계약서 전체 텍스트")


class RiskClause(BaseModel):
    sentence: str
    keyword: str
    reason: str


class AnalyzeResponse(BaseModel):
    total_sentences: int
    risk_count: int
    risk_clauses: list[RiskClause]
    summary: str
