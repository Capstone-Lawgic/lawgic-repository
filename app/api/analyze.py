from logging import getLogger

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.contract_domain import ContractDomain
from app.schemas.contract import AnalyzeResponse, ContractAnalyzeRequest
from app.services.contract_service import analyze_contract_text
from app.services.file_text_service import extract_text_from_upload

router = APIRouter(prefix="/api", tags=["analyze"])
logger = getLogger("uvicorn.error")


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_contract(payload: ContractAnalyzeRequest) -> AnalyzeResponse:
    return analyze_contract_text(payload.text, contract_type=payload.contract_type)


@router.post("/analyze-file", response_model=AnalyzeResponse)
async def analyze_contract_file(
    file: UploadFile = File(...),
    contract_type: ContractDomain | None = Form(default=None),
) -> AnalyzeResponse:
    try:
        text = await extract_text_from_upload(file)
        return analyze_contract_text(text, contract_type=contract_type)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("File analysis failed")
        raise HTTPException(
            status_code=500,
            detail="파일 분석 중 서버 오류가 발생했습니다. 서버 로그를 확인해 주세요.",
        ) from exc
