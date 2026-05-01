from app.core.config import settings


def generate_risk_summary(
    risk_count: int,
    total_sentences: int,
    context_chunks: list[str],
) -> str:
    """LLM 연동 전 임시 요약 함수.

    TODO:
    - provider 별 API 클라이언트 분기
    - system/user prompt 조합
    - 근거(context_chunks) 포함 요약 생성
    """
    _ = context_chunks
    if risk_count == 0:
        return f"총 {total_sentences}개 문장 중 위험 키워드는 발견되지 않았습니다."

    return (
        f"총 {total_sentences}개 문장 중 {risk_count}개의 잠재적 위험 조항이 탐지되었습니다. "
        f"(provider={settings.llm_provider}, model={settings.llm_model})"
    )
