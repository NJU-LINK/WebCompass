#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebCompass Unified Evaluation Script

Evaluates generated websites from three input modalities:
- Text-to-Web
- Image-to-Web
- Video-to-Web

Reads checklist.json files and computes accuracy metrics.
For Image tasks, run judge_image.py first to populate llm_score fields.

Usage:
    python -m generation.evaluation.evaluate --text_dir /path/to/text/results
    python -m generation.evaluation.evaluate --image_dir /path/to/image/results
    python -m generation.evaluation.evaluate --root /path/to/results
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Constants
# =============================================================================

CHECKLIST_FILE_MERGED = "checklist.json"

# Category mappings (support both old and new naming)
CATEGORY_ALIASES = {
    # New names -> Canonical
    "runnability": "Runnability",
    "spec implementation": "Spec Implementation",
    "spec_implementation": "Spec Implementation",
    "specimplementation": "Spec Implementation",
    "design quality": "Design Quality",
    "design_quality": "Design Quality",
    "designquality": "Design Quality",
    # Old names -> Canonical (mapped to new)
    "execution": "Runnability",
    "executability": "Runnability",
    "interaction": "Spec Implementation",
    "interactivity": "Spec Implementation",
    "aesthetics": "Design Quality",
}

CANONICAL_CATEGORIES = ["Runnability", "Spec Implementation", "Design Quality"]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TaskScore:
    """Score for a single task/sample."""
    task_id: str
    modality: str  # 'text', 'image', 'video'
    path: str
    total_score: float
    max_score: float
    accuracy: Optional[float]
    harmonic_mean: Optional[float]
    by_category: Dict[str, Dict[str, float]] = field(default_factory=dict)
    num_items: int = 0
    error: Optional[str] = None


@dataclass
class EvalSummary:
    """Summary of evaluation results."""
    modality: str
    num_tasks: int
    avg_accuracy: Optional[float]
    avg_harmonic_mean: Optional[float]
    by_category_avg: Dict[str, float]
    task_scores: List[TaskScore]


# =============================================================================
# Utility Functions
# =============================================================================

def _safe_read_json(path: str) -> Optional[Any]:
    """Safely read JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _to_float_or_none(v: Any) -> Optional[float]:
    """Convert value to float, return None if fails."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v != v:  # NaN
            return None
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None


def _normalize_category(cat: Any) -> str:
    """Normalize category name to canonical form."""
    if cat is None:
        return "unknown"
    s = str(cat).strip().lower()
    return CATEGORY_ALIASES.get(s, s.title())


def _harmonic_mean(values: List[float]) -> Optional[float]:
    """Compute harmonic mean of values."""
    if not values:
        return None
    # Filter out zeros to avoid division by zero
    non_zero = [v for v in values if v > 0]
    if not non_zero:
        return 0.0
    return len(non_zero) / sum(1 / v for v in non_zero)


# =============================================================================
# Checklist Scoring
# =============================================================================

def _find_checklist(task_dir: str) -> Optional[str]:
    """Find checklist.json in task directory or resume_site subdirectory."""
    # Direct path
    direct = os.path.join(task_dir, CHECKLIST_FILE_MERGED)
    if os.path.isfile(direct):
        return direct

    # Check resume_site subdirectory
    resume_site = os.path.join(task_dir, "resume_site")
    if os.path.isdir(resume_site):
        for name in os.listdir(resume_site):
            subdir = os.path.join(resume_site, name)
            if os.path.isdir(subdir):
                candidate = os.path.join(subdir, CHECKLIST_FILE_MERGED)
                if os.path.isfile(candidate):
                    return candidate

    return None


def score_task_from_checklist(task_dir: str, modality: str) -> Optional[TaskScore]:
    """Score a task by reading its checklist.json."""
    task_id = os.path.basename(os.path.normpath(task_dir))

    checklist_path = _find_checklist(task_dir)
    if not checklist_path:
        return None

    data = _safe_read_json(checklist_path)
    if data is None:
        return None

    # Handle both list format and dict with items
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("items", data.get("checklist", []))
        if not items and "problem_statement" in data:
            ps = data["problem_statement"]
            if isinstance(ps, list):
                items = ps

    if not items:
        return None

    total_score = 0.0
    max_score = 0.0
    by_category: Dict[str, Dict[str, float]] = {}
    item_ratios: List[float] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        # Support both "score" and "llm_score" fields
        score_v = _to_float_or_none(item.get("score"))
        if score_v is None:
            score_v = _to_float_or_none(item.get("llm_score"))

        max_v = _to_float_or_none(item.get("max_score"))

        # Default max_score to 100 for llm_score items (Aesthetics)
        if max_v is None and item.get("llm_score") is not None:
            max_v = 100.0

        if score_v is None or max_v is None or max_v <= 0:
            continue

        cat = _normalize_category(item.get("category"))

        total_score += score_v
        max_score += max_v

        if cat not in by_category:
            by_category[cat] = {"score": 0.0, "max_score": 0.0}
        by_category[cat]["score"] += score_v
        by_category[cat]["max_score"] += max_v

        ratio = score_v / max_v
        item_ratios.append(ratio)

    if max_score <= 0:
        return None

    accuracy = total_score / max_score if max_score > 0 else None
    hm = _harmonic_mean(item_ratios)

    return TaskScore(
        task_id=task_id,
        modality=modality,
        path=task_dir,
        total_score=total_score,
        max_score=max_score,
        accuracy=accuracy,
        harmonic_mean=hm,
        by_category=by_category,
        num_items=len(item_ratios),
    )


# =============================================================================
# Directory Scanning
# =============================================================================

def iter_task_dirs(root: str) -> List[str]:
    """Iterate over task directories under root."""
    if not os.path.isdir(root):
        return []

    dirs = []
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if os.path.isdir(p) and not name.startswith('.'):
            dirs.append(p)

    # Sort numerically if possible
    def sort_key(p):
        name = os.path.basename(p)
        try:
            return (0, int(name))
        except ValueError:
            return (1, name)

    return sorted(dirs, key=sort_key)


# =============================================================================
# Main Evaluation
# =============================================================================

def evaluate_modality(root: str, modality: str) -> EvalSummary:
    """Evaluate all tasks for a single modality."""
    task_dirs = iter_task_dirs(root)

    if not task_dirs:
        return EvalSummary(
            modality=modality,
            num_tasks=0,
            avg_accuracy=None,
            avg_harmonic_mean=None,
            by_category_avg={},
            task_scores=[],
        )

    scores: List[TaskScore] = []
    for task_dir in task_dirs:
        score = score_task_from_checklist(task_dir, modality)
        if score:
            scores.append(score)

    if not scores:
        return EvalSummary(
            modality=modality,
            num_tasks=0,
            avg_accuracy=None,
            avg_harmonic_mean=None,
            by_category_avg={},
            task_scores=[],
        )

    # Compute averages
    valid_acc = [s.accuracy for s in scores if s.accuracy is not None]
    valid_hm = [s.harmonic_mean for s in scores if s.harmonic_mean is not None]

    avg_acc = sum(valid_acc) / len(valid_acc) if valid_acc else None
    avg_hm = sum(valid_hm) / len(valid_hm) if valid_hm else None

    # Compute by-category averages
    cat_scores: Dict[str, List[float]] = {}
    for s in scores:
        for cat, data in s.by_category.items():
            if data["max_score"] > 0:
                cat_scores.setdefault(cat, []).append(data["score"] / data["max_score"])

    by_category_avg = {
        cat: sum(vals) / len(vals) if vals else 0.0
        for cat, vals in cat_scores.items()
    }

    return EvalSummary(
        modality=modality,
        num_tasks=len(scores),
        avg_accuracy=avg_acc,
        avg_harmonic_mean=avg_hm,
        by_category_avg=by_category_avg,
        task_scores=scores,
    )


def print_summary(summary: EvalSummary) -> None:
    """Print evaluation summary."""
    print(f"\n{'='*60}")
    print(f"Modality: {summary.modality.upper()}")
    print(f"{'='*60}")
    print(f"Tasks evaluated: {summary.num_tasks}")

    if summary.avg_accuracy is not None:
        print(f"Average accuracy: {summary.avg_accuracy:.4f} ({summary.avg_accuracy*100:.2f}%)")
    if summary.avg_harmonic_mean is not None:
        print(f"Average harmonic mean: {summary.avg_harmonic_mean:.4f}")

    if summary.by_category_avg:
        print("\nBy category:")
        for cat in CANONICAL_CATEGORIES:
            if cat in summary.by_category_avg:
                val = summary.by_category_avg[cat]
                print(f"  {cat}: {val:.4f} ({val*100:.2f}%)")


def save_results(summaries: List[EvalSummary], output_dir: str) -> None:
    """Save evaluation results to JSON and CSV files."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save JSON
    json_path = os.path.join(output_dir, f"eval_results_{timestamp}.json")
    results = []
    for s in summaries:
        results.append({
            "modality": s.modality,
            "num_tasks": s.num_tasks,
            "avg_accuracy": s.avg_accuracy,
            "avg_harmonic_mean": s.avg_harmonic_mean,
            "by_category_avg": s.by_category_avg,
            "task_scores": [
                {
                    "task_id": t.task_id,
                    "accuracy": t.accuracy,
                    "harmonic_mean": t.harmonic_mean,
                    "by_category": t.by_category,
                    "error": t.error,
                }
                for t in s.task_scores
            ],
        })

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON results saved to: {json_path}")

    # Save CSV
    csv_path = os.path.join(output_dir, f"eval_summary_{timestamp}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "modality", "task_id", "accuracy", "harmonic_mean",
            "Runnability", "Spec Implementation", "Design Quality", "error"
        ])
        for s in summaries:
            for t in s.task_scores:
                row = [
                    t.modality,
                    t.task_id,
                    f"{t.accuracy:.4f}" if t.accuracy else "",
                    f"{t.harmonic_mean:.4f}" if t.harmonic_mean else "",
                ]
                for cat in CANONICAL_CATEGORIES:
                    if cat in t.by_category and t.by_category[cat]["max_score"] > 0:
                        val = t.by_category[cat]["score"] / t.by_category[cat]["max_score"]
                        row.append(f"{val:.4f}")
                    else:
                        row.append("")
                row.append(t.error or "")
                writer.writerow(row)
    print(f"CSV summary saved to: {csv_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="WebCompass Evaluation Script - Calculate scores from checklist.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Input directories
    parser.add_argument("--text_dir", type=str, help="Directory with text-to-web results")
    parser.add_argument("--image_dir", type=str, help="Directory with image-to-web results")
    parser.add_argument("--video_dir", type=str, help="Directory with video-to-web results")
    parser.add_argument("--root", type=str, help="Single root directory (auto-detect modality)")

    # Output options
    parser.add_argument("--output_dir", type=str, default="./eval_output", help="Output directory")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")

    args = parser.parse_args()

    # Collect directories to evaluate
    dirs_to_eval: List[Tuple[str, str]] = []  # (path, modality)

    if args.root:
        dirs_to_eval.append((args.root, "auto"))
    if args.text_dir:
        dirs_to_eval.append((args.text_dir, "text"))
    if args.image_dir:
        dirs_to_eval.append((args.image_dir, "image"))
    if args.video_dir:
        dirs_to_eval.append((args.video_dir, "video"))

    if not dirs_to_eval:
        parser.print_help()
        print("\nError: Please specify at least one directory to evaluate.")
        return 1

    # Evaluate each modality
    summaries: List[EvalSummary] = []

    for path, modality in dirs_to_eval:
        if not os.path.isdir(path):
            print(f"Warning: Directory not found: {path}")
            continue

        print(f"\nEvaluating {modality} from: {path}")
        summary = evaluate_modality(root=path, modality=modality)
        summaries.append(summary)

        if not args.quiet:
            print_summary(summary)

    # Print overall summary
    if len(summaries) > 1:
        print(f"\n{'='*60}")
        print("OVERALL SUMMARY")
        print(f"{'='*60}")

        total_tasks = sum(s.num_tasks for s in summaries)
        all_acc = [s.avg_accuracy for s in summaries if s.avg_accuracy is not None]
        overall_acc = sum(all_acc) / len(all_acc) if all_acc else None

        print(f"Total tasks: {total_tasks}")
        if overall_acc is not None:
            print(f"Overall accuracy: {overall_acc:.4f} ({overall_acc*100:.2f}%)")

    # Save results
    if summaries:
        save_results(summaries, args.output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
