def generate_risk_summary(risk_count: int, total_sentences: int) -> str:
    """향후 LLM API 호출 로직으로 교체될 자리.

    현재는 단순 문자열 요약만 반환한다.
    """
    if risk_count == 0:
        return f"총 {total_sentences}개 문장 중 위험 키워드는 발견되지 않았습니다."

    return f"총 {total_sentences}개 문장 중 {risk_count}개의 잠재적 위험 조항이 탐지되었습니다."
