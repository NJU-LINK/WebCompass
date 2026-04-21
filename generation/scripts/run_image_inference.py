#!/usr/bin/env python3
"""
WebCompass Evaluation - Image-to-Web Inference

Generate web pages from reference screenshots.

Usage:
    python -m generation.scripts.run_image_inference \
        --data /path/to/checklist.jsonl \
        --images /path/to/images_root \
        --output /path/to/output \
        --model gpt-4o \
        --workers 4
"""

import argparse
import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from generation.inference import ImageToWebGenerator
from generation.utils import load_jsonl, append_jsonl
from generation.model_client import ModelClient


class Progress:
    """Simple progress tracker."""

    def __init__(self, total: int):
        self.total = total
        self.done = 0
        self.ok = 0
        self.error = 0
        self.skipped = 0
        self.start_time = time.time()
        self._lock = threading.Lock()

    def update(self, status: str):
        with self._lock:
            self.done += 1
            if status == "ok":
                self.ok += 1
            elif status == "skipped":
                self.skipped += 1
            else:
                self.error += 1
            self._render()

    def _render(self):
        elapsed = time.time() - self.start_time
        rate = self.done / max(elapsed, 0.001)
        eta = (self.total - self.done) / max(rate, 0.001)
        pct = self.done / self.total * 100

        msg = (
            f"\r[{self.done}/{self.total}] {pct:.1f}% "
            f"ok={self.ok} err={self.error} skip={self.skipped} "
            f"{rate:.2f}/s ETA {eta:.0f}s"
        )
        sys.stdout.write(msg + " " * 10)
        sys.stdout.flush()

    def close(self):
        self._render()
        sys.stdout.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Image-to-Web inference")
    parser.add_argument("--data", type=str, required=True, help="Path to JSONL data file with checklists")
    parser.add_argument("--images", type=str, required=True, help="Root directory containing screenshot folders")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    parser.add_argument("--base-url", type=str, default=None, help="API base URL")
    parser.add_argument("--api-key", type=str, default=None, help="API key")
    parser.add_argument("--model-id", type=str, default=None, help="Model ID for API calls")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries per item")
    parser.add_argument("--max-images", type=int, default=30, help="Max images per request (-1 for unlimited)")
    parser.add_argument("--id-key", type=str, default="instance_id", help="Key for ID field")
    parser.add_argument("--instruction-key", type=str, default="instance_id", help="Key for instruction/folder field")
    args = parser.parse_args()

    # Register model if custom config provided
    if args.base_url:
        ModelClient.register_model(
            name=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            model_id=args.model_id,
        )

    # Load data
    print(f"Loading data from: {args.data}")
    items = load_jsonl(args.data)
    print(f"Loaded {len(items)} items")

    # Setup output
    os.makedirs(args.output, exist_ok=True)
    log_path = os.path.join(args.output, "run_log.jsonl")

    # Create generator
    generator = ImageToWebGenerator(
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        model_id=args.model_id,
        max_retries=args.max_retries,
        max_images=args.max_images if args.max_images > 0 else 9999,
    )

    # Run inference
    print(f"Starting inference with {args.workers} workers...")
    progress = Progress(len(items))

    def process_item(item):
        result = generator.generate_from_item(
            item,
            images_root=args.images,
            output_base_dir=args.output,
            id_key=args.id_key,
            instruction_key=args.instruction_key,
        )
        append_jsonl(log_path, result)
        progress.update(result.get("status", "error"))
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_item, item) for item in items]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"\nError: {e}")

    progress.close()
    print(f"\nDone! Results saved to: {args.output}")
    print(f"Log file: {log_path}")


if __name__ == "__main__":
    main()
