"""Aggregate judge.json scores into per-folder / per-task-type / per-difficulty stats.

Edit and repair use different rubric dimensions (paper §F.5):
  edit   → instruction_targeting, feature_integrity,    style_conformance
  repair → root_cause_targeting,  interaction_integrity, reference_fidelity

`task_type` here always means the eval task ('edit' | 'repair'), NOT the
checklist category list inside info.json.
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List

low_bound = 1

DIM_NAMES: Dict[str, List[str]] = {
    "edit":   ["instruction_targeting", "feature_integrity",    "style_conformance"],
    "repair": ["root_cause_targeting",  "interaction_integrity", "reference_fidelity"],
}
DIM_LABELS: Dict[str, List[str]] = {
    "edit":   ["InstrTgt", "FeatInt", "StyleConf"],
    "repair": ["RootCause", "InterInt", "RefFid"],
}


def _dims(task_type: str) -> List[str]:
    if task_type not in DIM_NAMES:
        raise ValueError(f"Unknown task_type {task_type!r}; expected 'edit' or 'repair'")
    return DIM_NAMES[task_type]


def load_judge_results(
    results_path: str,
    task_type: str,
    page_category: str = "sp",
) -> List[Dict[str, Any]]:
    """Load every judge.json + info.json under {results_path}/{page_category}/.

    New layout: results/<task>/<session>/<page_category>/<case>/judge.json
    `task_type` selects the rubric dimensions but is no longer a subdir name.
    """
    task_path = Path(results_path) / page_category
    if not task_path.exists():
        print(f"Warning: {page_category} path not found: {task_path}")
        return []

    results = []
    for folder in sorted(task_path.iterdir()):
        if not folder.is_dir():
            continue
        judge_file = folder / "judge.json"
        info_file = folder / "info.json"
        if not (judge_file.exists() and info_file.exists()):
            continue
        try:
            with open(judge_file, "r", encoding="utf-8") as f:
                judge_data = json.load(f)
            with open(info_file, "r", encoding="utf-8") as f:
                info_data = json.load(f)
            if "judge_result" in judge_data and "task_type" in info_data:
                results.append({
                    "page_category": page_category,
                    "folder_name": folder.name,
                    "judge_result": judge_data["judge_result"],
                    "task_type": info_data["task_type"],
                })
        except Exception as e:
            print(f"Error loading {judge_file} or {info_file}: {e}")

    return results


def _harmonic_mean(values: List[float]) -> float:
    vals = [v for v in values if v > 0]
    return len(vals) / sum(1.0 / max(v, low_bound) for v in vals) if vals else 0.0


def calculate_statistics(
    results: List[Dict[str, Any]],
    task_type: str,
) -> Dict[str, Any]:
    """Compute folder / task-type / difficulty harmonic stats for one task family."""
    dims = _dims(task_type)
    d1, d2, d3 = dims

    folder_scores: Dict[str, Any] = {}
    task_type_overall: Dict[str, List[float]] = defaultdict(list)
    task_type_per_dim: Dict[str, Dict[str, List[float]]] = {
        d: defaultdict(list) for d in dims
    }

    difficulty_overall: Dict[int, List[float]] = defaultdict(list)
    difficulty_per_dim: Dict[str, Dict[int, List[float]]] = {
        d: defaultdict(list) for d in dims
    }

    for result in results:
        folder_name = result["folder_name"]
        task_scores = result["judge_result"].get("task_scores", [])
        difficulty = len(result["task_type"])

        if not task_scores:
            print(f"Warning: No task scores found for folder {folder_name}")
            continue

        per_task_hm = [
            3 / (
                1 / max(t[d1], low_bound) +
                1 / max(t[d2], low_bound) +
                1 / max(t[d3], low_bound)
            )
            for t in task_scores
        ]

        folder_overall_hm = _harmonic_mean(per_task_hm)
        folder_dim_hm = {
            d: _harmonic_mean([max(t[d], low_bound) for t in task_scores])
            for d in dims
        }

        sorted_hm = sorted(per_task_hm)
        n_tasks = len(sorted_hm)

        folder_entry = {
            "harmonic_mean": folder_overall_hm,
            "worst_of_1": sorted_hm[0],
            "worst_of_5": sum(sorted_hm[:5]) / min(5, n_tasks),
            "worst_half_tasks": sum(sorted_hm[: n_tasks // 2]) / max(1, n_tasks // 2),
            "num_tasks": n_tasks,
            "difficulty": difficulty,
            "harmonic_scores": per_task_hm,
        }
        for d in dims:
            folder_entry[f"harmonic_{d}"] = folder_dim_hm[d]
        folder_scores[f"{result['page_category']}_{folder_name}"] = folder_entry

        difficulty_overall[difficulty].append(folder_overall_hm)
        for d in dims:
            difficulty_per_dim[d][difficulty].append(folder_dim_hm[d])

        for t in task_scores:
            t_hm = 3 / (
                1 / max(t[d1], low_bound) +
                1 / max(t[d2], low_bound) +
                1 / max(t[d3], low_bound)
            )
            tt = t.get("task_type", "Unknown")
            task_type_overall[tt].append(t_hm)
            for d in dims:
                task_type_per_dim[d][tt].append(t[d])

    task_type_avg: Dict[str, Any] = {}
    for tt, scores in task_type_overall.items():
        entry = {
            "harmonic_mean": sum(scores) / len(scores) if scores else 0,
            "count": len(scores),
            "scores": scores,
        }
        for d in dims:
            vals = task_type_per_dim[d][tt]
            entry[f"avg_{d}"] = sum(vals) / len(vals) if vals else 0
        task_type_avg[tt] = entry

    difficulty_avg: Dict[int, Any] = {}
    for diff, scores in difficulty_overall.items():
        entry = {
            "harmonic_mean": sum(scores) / len(scores) if scores else 0,
            "count": len(difficulty_per_dim[d1][diff]),
            "num_folders": sum(
                1 for data in folder_scores.values() if data["difficulty"] == diff
            ),
        }
        for d in dims:
            vals = difficulty_per_dim[d][diff]
            entry[f"harmonic_{d}"] = sum(vals) / len(vals) if vals else 0
        difficulty_avg[diff] = entry

    folder_overall_list = [data["harmonic_mean"] for data in folder_scores.values()]
    overall_harmonic_mean = (
        sum(folder_overall_list) / len(folder_overall_list)
        if folder_overall_list else 0
    )

    def _avg(key: str) -> float:
        vals = [d[key] for d in folder_scores.values()]
        return sum(vals) / len(vals) if vals else 0

    overall_dim_harmonic = {
        f"overall_{d}_harmonic": _avg(f"harmonic_{d}") for d in dims
    }

    out = {
        "task_type": task_type,
        "dim_names": dims,
        "folder_scores": folder_scores,
        "task_type_scores": task_type_avg,
        "difficulty_scores": difficulty_avg,
        "overall_harmonic_mean": overall_harmonic_mean,
        "overall_worst_of_1": _avg("worst_of_1"),
        "overall_worst_of_5": _avg("worst_of_5"),
        "overall_worst_half_tasks": _avg("worst_half_tasks"),
        "total_folders": len(folder_scores),
        **overall_dim_harmonic,
    }
    return out


def print_statistics(stats: Dict[str, Any], task_type: str) -> None:
    dims = _dims(task_type)
    labels = DIM_LABELS[task_type]

    print(f"\n{'='*80}")
    print(f"{task_type.upper()} Task Statistics")
    print(f"{'='*80}")

    print(f"\n📊 Overall Statistics:")
    print(f"  Total Folders: {stats['total_folders']}")
    print(f"  Overall Harmonic Mean: {stats['overall_harmonic_mean']:.4f}")
    print(f"  Overall Worst-of-1 (HM): {stats['overall_worst_of_1']:.4f}")
    print(f"  Overall Worst-of-5 (HM): {stats['overall_worst_of_5']:.4f}")
    print(f"  Overall Worst Half Tasks (HM): {stats['overall_worst_half_tasks']:.4f}")
    for d, lab in zip(dims, labels):
        key = f"overall_{d}_harmonic"
        if key in stats:
            print(f"  Overall {lab} (HM): {stats[key]:.4f}")


    print(f"\n🎯 Task Type Harmonic Scores:")
    header = "Task Type\tHM\t\t" + "\t\t".join(labels) + "\t\tCount"
    print(header)
    for tt, data in sorted(stats["task_type_scores"].items(), key=lambda x: x[0]):
        per_dim = "\t\t".join(f"{data[f'avg_{d}']:.4f}" for d in dims)
        print(f"{tt}\t{data['harmonic_mean']:.4f}\t\t{per_dim}\t\t{data['count']}")


def save_statistics_to_json(stats: Dict[str, Any], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Statistics saved to: {output_path}")
