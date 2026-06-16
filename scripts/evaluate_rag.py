import argparse
import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT_DIR / "app" / "data" / "eval" / "rag_eval_cases.json"

import sys

sys.path.insert(0, str(ROOT_DIR))

from app.services.rag_service import retrieve_related_context  # noqa: E402


def _contains(value: str | None, expected: str | None) -> bool:
    if not expected:
        return True
    return expected.lower() in (value or "").lower()


def _matches_expected(result: Any, case: dict[str, Any]) -> bool:
    source_expected = case.get("expected_source_contains")
    title_expected = case.get("expected_title_contains")
    if source_expected or title_expected:
        return _contains(result.source, source_expected) and _contains(
            result.title,
            title_expected,
        )

    return any(
        keyword in result.title or keyword in result.content or keyword in result.source
        for keyword in case.get("expected_keywords", [])
    )


def _load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Eval cases file must contain a JSON array.")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--domain",
        choices=["employment", "lease"],
        default="employment",
        help="RAG context domain to evaluate.",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--show", action="store_true", help="Print retrieved contexts for each case.")
    args = parser.parse_args()

    if args.top_k <= 0:
        raise SystemExit("--top-k must be greater than 0.")
    if not args.cases.exists():
        raise SystemExit(f"Eval cases file does not exist: {args.cases}")

    cases = _load_cases(args.cases)
    top1_hits = 0
    topk_hits = 0

    for index, case in enumerate(cases, start=1):
        query = case.get("input", "")
        if not isinstance(query, str) or not query.strip():
            raise SystemExit(f"Case {index} has empty input.")

        results = retrieve_related_context(query, contract_type=args.domain, top_k=args.top_k)
        matches = [_matches_expected(result, case) for result in results]
        top1_hit = bool(matches[:1] and matches[0])
        topk_hit = any(matches)
        top1_hits += int(top1_hit)
        topk_hits += int(topk_hit)

        status = "PASS" if topk_hit else "FAIL"
        print(f"[{status}] case {index}: {query}")
        print(f"  top1_hit={top1_hit} top{args.top_k}_hit={topk_hit}")

        if args.show:
            for rank, result in enumerate(results, start=1):
                marker = "*" if matches[rank - 1] else "-"
                print(
                    f"  {marker} {rank}. {result.title} | {result.source} | score={result.score}"
                )

    total = len(cases)
    top1_accuracy = top1_hits / total if total else 0.0
    topk_accuracy = topk_hits / total if total else 0.0
    print()
    print(f"Cases: {total}")
    print(f"Top-1 accuracy: {top1_accuracy:.1%} ({top1_hits}/{total})")
    print(f"Top-{args.top_k} accuracy: {topk_accuracy:.1%} ({topk_hits}/{total})")


if __name__ == "__main__":
    main()
