#!/usr/bin/env python3
"""Generate checklists from text design documents.

Usage:
    python -m generation.scripts.generate_text_checklist \
        --input /path/to/data.jsonl \
        --output /path/to/output.jsonl \
        --model Gemini-3-Pro \
        --workers 10
"""

import argparse
import json
from pathlib import Path

from tqdm import tqdm

from generation.checklist import TextChecklistGenerator


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate evaluation checklists from text design documents"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="Input JSONL file with design documents",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Output JSONL file with checklists",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="Gemini-3-Pro",
        help="Model to use for generation (default: Gemini-3-Pro)",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=10,
        help="Number of parallel workers (default: 10)",
    )
    parser.add_argument(
        "--instruction-key",
        type=str,
        default="instruction",
        help="Key containing the instruction/design document (default: instruction)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of items to process (for testing)",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list:
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def main():
    args = parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    print(f"Loading data from: {args.input}")
    items = load_jsonl(args.input)

    if args.limit:
        items = items[:args.limit]

    print(f"Loaded {len(items)} items")
    print(f"Using model: {args.model}")
    print(f"Workers: {args.workers}")

    generator = TextChecklistGenerator(
        model=args.model,
        max_workers=args.workers,
    )

    results = generator.generate_batch(
        items,
        instruction_key=args.instruction_key,
        output_path=args.output,
    )

    print(f"\nGenerated {len(results)} checklists")
    print(f"Output written to: {args.output}")


if __name__ == "__main__":
    main()
