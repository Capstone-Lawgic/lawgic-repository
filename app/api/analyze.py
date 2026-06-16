from fastapi import APIRouter, File, UploadFile

from app.schemas.contract import AnalyzeResponse, ContractAnalyzeRequest
from app.services.contract_service import analyze_contract_text
from app.services.file_text_service import extract_text_from_upload

router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_contract(payload: ContractAnalyzeRequest) -> AnalyzeResponse:
    return analyze_contract_text(payload.text)


@router.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_contract_file(file: UploadFile = File(...)) -> AnalyzeResponse:
    text = await extract_text_from_upload(file)
    return analyze_contract_text(text)
