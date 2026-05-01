SYSTEM_PROMPT = """\
너는 한국어 계약서 리스크 분석 보조 시스템이다.
출력에는 위험 문장, 위험 사유, 개선 제안을 구조화해서 포함한다.
"""

USER_PROMPT_TEMPLATE = """\
[계약서 텍스트]
{text}

[탐지된 잠재 위험 조항]
{risk_lines}

[참고 컨텍스트]
{contexts}
"""
