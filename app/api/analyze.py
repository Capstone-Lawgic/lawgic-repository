from fastapi import APIRouter

from app.schemas.contract import AnalyzeResponse, ContractAnalyzeRequest
from app.services.contract_service import analyze_contract_text

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_contract(payload: ContractAnalyzeRequest) -> AnalyzeResponse:
    return analyze_contract_text(payload.text)
