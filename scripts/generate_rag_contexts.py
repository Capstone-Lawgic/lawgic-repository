import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT_DIR / "app" / "data" / "raw" / "law_sources.json"
DEFAULT_OUTPUT = ROOT_DIR / "app" / "data" / "generated" / "labor_law_contexts.generated.json"
APP_CONTEXTS = ROOT_DIR / "app" / "data" / "labor_law_contexts.json"
DEFAULT_MODEL = "gpt-5.4-mini"
MAX_SOURCE_CHARS = 18000
EXCLUDE_TERMS = [
    "명단공개",
    "명단 공개",
    "자료 제공",
    "자료제공",
    "자료 열람",
    "열람",
    "복사",
    "업무위탁",
    "업무 위탁",
    "지원 제한",
    "보조",
    "출국금지",
    "국내대리인",
    "대리인 지정",
    "조사",
    "시정명령",
    "과태료",
    "벌칙",
    "양벌규정",
    "미수",
    "예비",
    "음모",
    "몰수",
    "공소시효",
    "지리적 표시",
    "부칙",
    "개정문",
    "제개정이유",
    "별표",
    "서식",
    "연락부서",
    "연차휴가",
    "출산전후휴가",
    "임신기",
    "신용회복",
]
INCLUDE_TERMS = [
    "위약금",
    "위약",
    "손해배상",
    "배상",
    "퇴사",
    "계약해지",
    "계약 해지",
    "교육비",
    "임금",
    "최저임금",
    "기본급",
    "수당",
    "공제",
    "수습",
    "포괄임금",
    "근로시간",
    "연장근로",
    "야간근로",
    "휴일근로",
    "휴게시간",
    "가산수당",
    "해고",
    "즉시 해고",
    "정당한 이유",
    "징계",
    "개인정보",
    "수집",
    "이용",
    "보유기간",
    "보유 기간",
    "제3자 제공",
    "동의",
    "비밀유지",
    "비밀 유지",
    "영업비밀",
    "경업금지",
    "동종업계",
    "퇴직 후",
    "보상",
    "근무장소",
    "근무 장소",
    "직무",
    "전보",
    "배치전환",
    "일방적 변경",
    "근로조건",
]


class RagContext(BaseModel):
    source: str = Field(description="Official source name and article/case identifier.")
    title: str = Field(description="Short title for the RAG context.")
    content: str = Field(description="Contract-review summary grounded only in the source.")
    keywords: list[str] = Field(description="Contract phrases likely to match this source.")
    category: str = Field(description="Risk category for contract review.")
    risk_level: str = Field(description="One of low, medium, high.")
    source_url: str | None = Field(default=None)


class RagContextBatch(BaseModel):
    contexts: list[RagContext]


def _collect_text(value: Any, parts: list[str]) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _collect_text(item, parts)
    elif isinstance(value, list):
        for item in value:
            _collect_text(item, parts)
    elif isinstance(value, str):
        text = " ".join(value.split())
        if text:
            parts.append(text)
    elif isinstance(value, (int, float)):
        parts.append(str(value))


def _source_to_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    _collect_text(record, parts)
    text = "\n".join(parts)
    return text[:MAX_SOURCE_CHARS]


def _generate_contexts_for_source(
    client: OpenAI,
    model: str,
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    source_text = _source_to_text(record)
    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "너는 한국 근로계약서 RAG 데이터 구축 보조자다. "
                    "제공된 공식 원문 안에 있는 내용만 근거로 사용한다. "
                    "원문에 없는 법령명, 조문번호, 판례, 법적 결론을 만들지 않는다. "
                    "계약서 조항의 위험 여부를 판단하는 데 직접 도움이 되는 근거만 선별한다. "
                    "행정절차, 기관 권한, 자료제공, 업무위탁, 명단공개, 벌칙, 과태료, 부칙, "
                    "개정이유처럼 계약서 문구 검토와 직접 관련 없는 항목은 제외한다."
                ),
            },
            {
                "role": "user",
                "content": (
                    "다음 공식 원문 payload를 계약서 검토용 RAG JSON으로 변환하라.\n"
                    "목표는 근로계약서, 프리랜서 계약서, 입사/퇴사 관련 약정에서 "
                    "위험 조항을 찾을 때 검색될 근거 데이터를 만드는 것이다.\n\n"
                    "우선 포함할 위험 유형:\n"
                    "- 위약금/손해배상 예정: 퇴사, 계약해지, 교육비 반환, 정액 배상\n"
                    "- 임금/최저임금: 기본급, 수당, 공제, 수습, 포괄임금\n"
                    "- 근로시간: 연장근로, 야간근로, 휴일근로, 휴게시간, 가산수당\n"
                    "- 해고/계약해지: 즉시 해고, 일방적 종료, 정당한 이유, 징계\n"
                    "- 개인정보: 개인정보 수집, 이용, 보유기간, 제3자 제공, 동의\n"
                    "- 비밀유지/경업금지: 영업비밀, 동종업계 취업 제한, 퇴직 후 제한, 보상\n"
                    "- 근로조건 변경: 근무장소, 직무, 전보, 배치전환, 일방적 변경\n\n"
                    "제외할 항목:\n"
                    "- 벌칙, 과태료, 양벌규정, 미수, 예비ㆍ음모\n"
                    "- 행정기관의 조사, 자료제공 요청, 업무위탁, 지원 제한, 명단공개\n"
                    "- 부칙, 개정문, 제개정이유, 별표, 서식, 연락부서 정보\n"
                    "- 계약서 조항의 위험 판단과 연결하기 어려운 일반 선언 조항\n\n"
                    "요구사항:\n"
                    "- contexts는 0~8개만 생성한다. 적절한 근거가 없으면 빈 배열을 반환한다.\n"
                    "- source에는 반드시 법령명과 조문번호를 함께 적는다. 예: 근로기준법 제20조\n"
                    "- title은 계약서 검토자가 이해할 수 있는 짧은 위험 주제로 쓴다.\n"
                    "- content는 원문을 그대로 복사하지 말고 계약서 검토 관점으로 1~2문장 요약한다.\n"
                    "- keywords는 법률 용어뿐 아니라 계약서에 실제로 나올 표현을 포함한다.\n"
                    "- keywords는 5~12개로 작성하고, 지나치게 일반적인 단어만 넣지 않는다.\n"
                    "- category는 위 우선 위험 유형 중 가장 가까운 이름으로 작성한다.\n"
                    "- risk_level은 low, medium, high 중 하나만 사용한다.\n"
                    "- 근거가 불명확하거나 조문번호를 특정하기 어렵다면 생성하지 않는다.\n"
                    "- 서로 비슷한 context를 중복 생성하지 않는다.\n\n"
                    f"[공식 원문 payload]\n{source_text}"
                ),
            },
        ],
        text_format=RagContextBatch,
    )
    return [context.model_dump() for context in response.output_parsed.contexts]


def _dedupe_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for context in contexts:
        key = (context["source"], context["title"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(context)
    return deduped


def _context_search_text(context: dict[str, Any]) -> str:
    keywords = context.get("keywords", [])
    if isinstance(keywords, list):
        keyword_text = " ".join(str(keyword) for keyword in keywords)
    else:
        keyword_text = str(keywords)

    return " ".join(
        [
            str(context.get("source", "")),
            str(context.get("title", "")),
            str(context.get("content", "")),
            str(context.get("category", "")),
            keyword_text,
        ]
    )


def _is_contract_relevant(context: dict[str, Any]) -> bool:
    text = _context_search_text(context)
    if any(term in text for term in EXCLUDE_TERMS):
        return False
    return any(term in text for term in INCLUDE_TERMS)


def _filter_contexts(contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [context for context in contexts if _is_contract_relevant(context)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate labor-law RAG contexts from collected source payloads."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model for generation. Defaults to OPENAI_MODEL or gpt-5.4-mini.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Also replace app/data/labor_law_contexts.json after generation.",
    )
    args = parser.parse_args()

    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in .env before generating RAG contexts.")
    if not args.input.exists():
        raise SystemExit(f"Input source file does not exist: {args.input}")

    model = args.model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    records = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("Input source file must be a JSON array.")

    client = OpenAI()
    contexts: list[dict[str, Any]] = []
    for record in records:
        contexts.extend(_generate_contexts_for_source(client, model, record))

    generated_count = len(contexts)
    contexts = _filter_contexts(_dedupe_contexts(contexts))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(contexts, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if args.apply:
        shutil.copyfile(args.output, APP_CONTEXTS)

    print(
        f"Wrote {len(contexts)} generated contexts to {args.output} "
        f"({generated_count - len(contexts)} filtered out)"
    )
    if args.apply:
        print(f"Updated {APP_CONTEXTS}")


if __name__ == "__main__":
    main()
