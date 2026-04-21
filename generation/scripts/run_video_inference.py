#!/usr/bin/env python3
"""
WebCompass Evaluation - Video-to-Web Inference

Generate web pages from video demonstrations.

Usage:
    python -m generation.scripts.run_video_inference \
        --input /path/to/videos_dir \
        --output /path/to/output \
        --model gpt-4o \
        --workers 4
"""

import argparse
import sys
import os
import glob
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from generation.inference import VideoToWebGenerator
from generation.utils import append_jsonl
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


def find_videos(input_dir: str) -> list:
    """Find all supported video files in a directory."""
    supported_formats = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
    video_files = []

    for ext in supported_formats:
        pattern = os.path.join(input_dir, f"*{ext}")
        video_files.extend(glob.glob(pattern))
        # Also scan subdirectories
        pattern = os.path.join(input_dir, f"**/*{ext}")
        video_files.extend(glob.glob(pattern, recursive=True))

    return sorted(list(set(video_files)))


def main():
    parser = argparse.ArgumentParser(description="Video-to-Web inference")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing videos")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--model", type=str, required=True, help="Model name")
    parser.add_argument("--base-url", type=str, default=None, help="API base URL")
    parser.add_argument("--api-key", type=str, default=None, help="API key")
    parser.add_argument("--model-id", type=str, default=None, help="Model ID for API calls")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--max-retries", type=int, default=5, help="Max retries per video")
    parser.add_argument("--target-fps", type=float, default=3.0, help="Target FPS for frame extraction")
    parser.add_argument("--max-frames", type=int, default=60, help="Maximum frames to extract")
    parser.add_argument("--sample-size", type=int, default=0, help="Random sample size (0 for all)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for sampling")
    args = parser.parse_args()

    # Register model if custom config provided
    if args.base_url:
        ModelClient.register_model(
            name=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            model_id=args.model_id,
        )

    # Find videos
    print(f"Scanning for videos in: {args.input}")
    videos = find_videos(args.input)
    print(f"Found {len(videos)} videos")

    if not videos:
        print("No videos found!")
        return 1

    # Sample if requested
    if args.sample_size > 0 and len(videos) > args.sample_size:
        if args.seed is not None:
            random.seed(args.seed)
        videos = random.sample(videos, args.sample_size)
        print(f"Sampled {args.sample_size} videos")

    # Setup output
    model_output = os.path.join(args.output, args.model.replace("/", "_"))
    os.makedirs(model_output, exist_ok=True)
    log_path = os.path.join(model_output, "run_log.jsonl")

    # Create generator
    generator = VideoToWebGenerator(
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        model_id=args.model_id,
        max_retries=args.max_retries,
        target_fps=args.target_fps,
        max_frames=args.max_frames,
    )

    # Run inference
    print(f"Starting inference with {args.workers} workers...")
    progress = Progress(len(videos))

    def process_video(video_path):
        result = generator.generate_from_video_file(video_path, model_output)
        append_jsonl(log_path, result)
        progress.update(result.get("status", "error"))
        return result

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(process_video, video) for video in videos]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"\nError: {e}")

    progress.close()
    print(f"\nDone! Results saved to: {model_output}")
    print(f"Log file: {log_path}")


if __name__ == "__main__":
    main()
