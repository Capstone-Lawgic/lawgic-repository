import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "app" / "data" / "raw" / "law_sources.json"
LAW_SEARCH_URL = "https://www.law.go.kr/DRF/lawSearch.do"
LAW_SERVICE_URL = "https://www.law.go.kr/DRF/lawService.do"

DEFAULT_LAWS = [
    "근로기준법",
    "최저임금법",
    "개인정보 보호법",
    "부정경쟁방지 및 영업비밀보호에 관한 법률",
]


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _find_first_law(search_result: dict[str, Any]) -> dict[str, Any] | None:
    law_items = search_result.get("LawSearch", {}).get("law")
    items = _as_list(law_items)
    return items[0] if items else None


def _collect_law(oc: str, law_name: str) -> dict[str, Any]:
    search_result = _request_json(
        LAW_SEARCH_URL,
        {
            "OC": oc,
            "target": "law",
            "type": "JSON",
            "query": law_name,
            "display": 1,
        },
    )
    law = _find_first_law(search_result)
    if not law:
        raise RuntimeError(f"No law search result for {law_name}")

    law_id = law.get("법령ID") or law.get("ID")
    mst = law.get("법령일련번호") or law.get("MST")
    params = {
        "OC": oc,
        "target": "law",
        "type": "JSON",
    }
    if law_id:
        params["ID"] = law_id
    elif mst:
        params["MST"] = mst
    else:
        params["LM"] = law_name

    detail = _request_json(LAW_SERVICE_URL, params)
    return {
        "source_type": "law.go.kr",
        "query": law_name,
        "search_result": law,
        "detail": detail,
        "source_url": response_url_for_law(law_id=law_id, mst=mst, law_name=law_name),
    }


def response_url_for_law(
    law_id: str | None,
    mst: str | None,
    law_name: str,
) -> str:
    if law_id:
        return f"https://www.law.go.kr/법령/{law_name}/(ID:{law_id})"
    if mst:
        return f"https://www.law.go.kr/법령/{law_name}/(MST:{mst})"
    return f"https://www.law.go.kr/법령/{law_name}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect official law source payloads from law.go.kr."
    )
    parser.add_argument(
        "--law",
        action="append",
        dest="laws",
        help="Law name to collect. Can be passed multiple times.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    load_dotenv()
    oc = os.getenv("LAW_API_OC")
    if not oc:
        raise SystemExit("Set LAW_API_OC in .env before collecting law.go.kr data.")

    laws = args.laws or DEFAULT_LAWS
    records = [_collect_law(oc, law_name) for law_name in laws]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(records)} source records to {args.output}")


if __name__ == "__main__":
    main()
