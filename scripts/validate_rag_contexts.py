import argparse
import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT_DIR / "app" / "data" / "generated" / "labor_law_contexts.generated.json"
REQUIRED_FIELDS = {"source", "title", "content", "keywords"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}


def _validate_context(context: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS - set(context)
    if missing:
        errors.append(f"[{index}] missing fields: {', '.join(sorted(missing))}")

    for field in ["source", "title", "content"]:
        value = context.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"[{index}] {field} must be a non-empty string")

    keywords = context.get("keywords")
    if not isinstance(keywords, list) or not keywords:
        errors.append(f"[{index}] keywords must be a non-empty list")
    elif any(not isinstance(keyword, str) or not keyword.strip() for keyword in keywords):
        errors.append(f"[{index}] keywords must contain only non-empty strings")

    risk_level = context.get("risk_level")
    if risk_level is not None and risk_level not in ALLOWED_RISK_LEVELS:
        errors.append(f"[{index}] risk_level must be one of low, medium, high")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated RAG context JSON.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file does not exist: {args.input}")

    data = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Input file must contain a JSON array.")

    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, context in enumerate(data):
        if not isinstance(context, dict):
            errors.append(f"[{index}] context must be an object")
            continue
        errors.extend(_validate_context(context, index))
        key = (str(context.get("source", "")), str(context.get("title", "")))
        if key in seen:
            errors.append(f"[{index}] duplicate source/title: {key[0]} / {key[1]}")
        seen.add(key)

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    print(f"Validated {len(data)} RAG contexts from {args.input}")


if __name__ == "__main__":
    main()
