import base64
import io
import os
import time
from logging import getLogger

from fastapi import HTTPException, UploadFile

from app.core.env import load_environment
from app.services.llm_service import DEFAULT_MODEL

load_environment()

logger = getLogger("uvicorn.error")

PDF_CONTENT_TYPES = {"application/pdf"}
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


async def extract_text_from_upload(file: UploadFile) -> str:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="업로드된 파일이 비어 있습니다.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="파일은 10MB 이하만 업로드할 수 있습니다.")

    content_type = (file.content_type or "").lower()
    filename = (file.filename or "").lower()

    if content_type in PDF_CONTENT_TYPES or filename.endswith(".pdf"):
        return _extract_text_from_pdf(content)

    if content_type in IMAGE_CONTENT_TYPES or filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return _extract_text_from_image(content, content_type)

    raise HTTPException(
        status_code=400,
        detail="PDF, JPG, PNG, WEBP 파일만 지원합니다.",
    )


def _extract_text_from_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="PDF 분석을 위해 pypdf 패키지를 설치해야 합니다. pip install -r requirements.txt",
        ) from exc

    start = time.perf_counter()
    try:
        reader = PdfReader(io.BytesIO(content))
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PDF text extraction failed")
        raise HTTPException(status_code=400, detail="PDF 텍스트를 읽지 못했습니다.") from exc

    text = "\n\n".join(page_text.strip() for page_text in page_texts if page_text.strip())
    logger.info(
        "analysis timing: extract_pdf_text=%.3fs page_count=%s text_chars=%s",
        time.perf_counter() - start,
        len(page_texts),
        len(text),
    )

    if not text:
        raise HTTPException(
            status_code=400,
            detail="PDF에서 텍스트를 추출하지 못했습니다. 스캔 PDF는 이미지로 변환해 업로드해 주세요.",
        )

    return text


def _extract_text_from_image(content: bytes, content_type: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="이미지 텍스트 추출에는 OPENAI_API_KEY가 필요합니다.",
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="openai 패키지를 설치해야 합니다.") from exc

    media_type = content_type if content_type in IMAGE_CONTENT_TYPES else "image/png"
    image_url = f"data:{media_type};base64,{base64.b64encode(content).decode('ascii')}"
    start = time.perf_counter()

    try:
        client = OpenAI()
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "이미지에 있는 한국어 계약서/문서 텍스트를 빠짐없이 추출하세요. "
                                "설명이나 요약 없이 원문 텍스트만 줄바꿈을 유지해 출력하세요."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": image_url,
                        },
                    ],
                }
            ],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Image text extraction failed")
        raise HTTPException(status_code=502, detail="이미지 텍스트 추출에 실패했습니다.") from exc

    text = response.output_text.strip()
    logger.info(
        "analysis timing: extract_image_text=%.3fs text_chars=%s",
        time.perf_counter() - start,
        len(text),
    )

    if not text:
        raise HTTPException(status_code=400, detail="이미지에서 텍스트를 추출하지 못했습니다.")

    return text
