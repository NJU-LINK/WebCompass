#!/usr/bin/env python3
"""Generate checklists from reference screenshots.

Usage:
    # Single sample
    python -m generation.scripts.generate_image_checklist \
        --screenshots /path/to/screenshots \
        --output /path/to/output \
        --id sample_001 \
        --model Gemini-3-Pro

    # Batch mode
    python -m generation.scripts.generate_image_checklist \
        --image-data-root /path/to/images_root \
        --output /path/to/output \
        --model Gemini-3-Pro \
        --workers 4
"""

import argparse
import json
import shutil
from pathlib import Path

from generation.checklist import ImageChecklistGenerator, generate_image_checklist
from generation.checklist.generator import list_images


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate evaluation checklists from reference screenshots"
    )
    # Single sample mode
    parser.add_argument(
        "--screenshots",
        type=Path,
        default=None,
        help="Path to screenshots directory (single sample mode)",
    )
    parser.add_argument(
        "--id",
        type=str,
        default=None,
        help="Sample ID (single sample mode)",
    )
    # Batch mode
    parser.add_argument(
        "--image-data-root",
        type=Path,
        default=None,
        help="Root directory containing sample subdirectories (batch mode)",
    )
    # Common options
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Output directory",
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
        default=4,
        help="Number of parallel workers for batch mode (default: 4)",
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=30,
        help="Maximum number of images to include (default: 30)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if output exists",
    )
    parser.add_argument(
        "--minimal-output",
        action="store_true",
        help="Only output checklist.jsonl, skip intermediate files",
    )
    return parser.parse_args()


def run_single_sample(
    screenshots_dir: Path,
    sample_id: str,
    output_root: Path,
    model: str,
    max_images: int,
    minimal_output: bool,
):
    """Process a single sample."""
    out_dir = output_root / sample_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage screenshots
    staged_screenshots = out_dir / "screenshots"
    staged_screenshots.mkdir(parents=True, exist_ok=True)
    for p in sorted(screenshots_dir.iterdir(), key=lambda x: x.name):
        if p.is_file():
            shutil.copy2(p, staged_screenshots / p.name)

    # List images
    images = list_images(staged_screenshots, max_images)
    if not images:
        print(f"[{sample_id}] WARN: No images found")
        return None

    # Generate checklist
    image_paths = [img.path for img in images]
    checklist = generate_image_checklist(image_paths, model=model)

    if checklist is None:
        print(f"[{sample_id}] WARN: Failed to parse checklist")
        return None

    # Write output
    if not minimal_output:
        (out_dir / "checklist.json").write_text(
            json.dumps(checklist, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # Build record
    record = {
        "meta": {"class": "image_generation", "difficulty": "N/A"},
        "working_dir": "/testbed",
        "repo": "claude/webcoding",
        "instance_id": sample_id,
        "base_commit": "main",
        "problem_statement": checklist,
        "instruction": sample_id,
    }

    # Append to global JSONL
    global_jsonl = output_root / "checklist.jsonl"
    with global_jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[{sample_id}] OK -> {global_jsonl}")
    return record


def main():
    args = parse_args()

    if args.image_data_root is not None:
        # Batch mode
        if not args.image_data_root.exists():
            raise FileNotFoundError(f"Image data root not found: {args.image_data_root}")

        print(f"Batch mode: scanning {args.image_data_root}")
        print(f"Using model: {args.model}")
        print(f"Workers: {args.workers}")

        generator = ImageChecklistGenerator(
            model=args.model,
            max_images=args.max_images,
            max_workers=args.workers,
        )

        results = generator.generate_batch(
            args.image_data_root,
            args.output,
            force=args.force,
        )

        print(f"\nGenerated {len(results)} checklists")
        print(f"Output: {args.output / 'checklist.jsonl'}")

    elif args.screenshots is not None:
        # Single sample mode
        if args.id is None:
            raise ValueError("--id is required in single sample mode")
        if not args.screenshots.exists():
            raise FileNotFoundError(f"Screenshots directory not found: {args.screenshots}")

        print(f"Single sample mode: {args.id}")
        print(f"Using model: {args.model}")

        run_single_sample(
            screenshots_dir=args.screenshots,
            sample_id=args.id,
            output_root=args.output,
            model=args.model,
            max_images=args.max_images,
            minimal_output=args.minimal_output,
        )

    else:
        raise ValueError("Either --image-data-root (batch) or --screenshots (single) is required")


if __name__ == "__main__":
    main()
