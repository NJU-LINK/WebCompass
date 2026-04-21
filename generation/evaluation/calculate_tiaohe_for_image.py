#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""统计 resume_site 下每个题目的 checklist 得分（按三类调和平均数）。

支持两种目录结构：

1) 新版：每题一个合并文件（优先）

resume_site/
    2/
        checklist.json
    105/
        ...

其中 checklist.json 里包含三类：Executability / Interactivity / Aesthetics。
脚本会把三类合并计分，并按 kind 与 category 统计。

2) 旧版：三文件拆分（兼容）

resume_site/
    2/
        checklist_Aesthetics.json
        checklist_Executability.json
        checklist_Interactivity.json

或更旧命名：

resume_site/
    2/
        checklist_aesthetics.json
        checklist_execution.json
        checklist_interaction.json

计分规则：
- 新格式 item：若包含 score/max_score，则按其累计；若 score 为 null/None 则整条跳过（不记分子/分母）
- 旧格式 item：status=="pass" 计 1 分，否则 0；status=="pending" 整条跳过

计分方式：
- 对每道题直接把所有 checklist 条目的准确率求调和平均数作为该题分数
- 若单条 checklist item 的分数为 0，则先将其加 1 再计算该条准确率
- 最后输出所有题的平均分（按有效题目平均）

输出：
- 控制台打印每题得分与总分
- 写出 summary.csv / summary.json 到 resume_site 根目录
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence


# New official filenames (preferred)
CHECKLIST_FILES = [
    "checklist_Aesthetics.json",
    "checklist_Executability.json",
    "checklist_Interactivity.json",
]

# New merged filename (preferred over all others)
CHECKLIST_FILE_MERGED = "checklist.json"

# Backward-compat filenames (older runs)
CHECKLIST_FILES_LEGACY = [
    "checklist_aesthetics.json",
    "checklist_execution.json",
    "checklist_interaction.json",
]


CHECKLIST_KIND_OF_FILE = {
    # new
    "checklist_Aesthetics.json": "Aesthetics",
    "checklist_Executability.json": "Executability",
    "checklist_Interactivity.json": "Interactivity",
    # legacy
    "checklist_aesthetics.json": "Aesthetics",
    "checklist_execution.json": "Executability",
    "checklist_interaction.json": "Interactivity",
}


def _normalize_kind(kind: Any) -> str:
    """归一化 checklist 维度名（兼容 Execution/Interaction 别名）。"""
    if kind is None:
        return "unknown"
    s = str(kind).strip()
    if not s:
        return "unknown"
    low = re.sub(r"[^a-z]", "", s.lower())
    if not low:
        return "unknown"
    if low == "execution" or low == "executability":
        return "Executability"
    if low == "interaction" or low == "interactivity":
        return "Interactivity"
    if low == "aesthetics":
        return "Aesthetics"
    return s


def _safe_read_json(path: str) -> Optional[Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _norm_status(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip().lower()


def _to_int_or_none(v: Any) -> Optional[int]:
    """尽量把 v 转成 int；失败返回 None。"""
    if v is None:
        return None
    if isinstance(v, bool):
        # 避免 True/False 被当成 1/0
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if v != v:  # NaN
            return None
        return int(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return int(float(s))
        except Exception:
            return None
    try:
        return int(v)
    except Exception:
        return None


@dataclass
class TaskScore:
    task_id: str
    path: str
    total_items: int
    passed_items: int
    score: Optional[float]
    max_score: float
    harmonic_mean: Optional[float]
    harmonic_mean_by_kind: Dict[str, Optional[float]]
    harmonic_mean_by_group: Dict[str, Optional[float]]
    by_category_total: Dict[str, int]
    by_category_passed: Dict[str, int]
    by_kind_total: Dict[str, int]
    by_kind_passed: Dict[str, int]


def score_one_task_dir(task_dir: str) -> Optional[TaskScore]:
    # 只统计包含任意 checklist 文件的目录
    found_any = False

    total_items = 0
    passed_items = 0
    by_cat_total: Dict[str, int] = {}
    by_cat_passed: Dict[str, int] = {}
    by_kind_total: Dict[str, int] = {}
    by_kind_passed: Dict[str, int] = {}
    item_ratios: List[float] = []
    item_ratios_by_kind: Dict[str, List[float]] = {}

    def _accumulate_item(*, item: Dict[str, Any], kind: str) -> None:
        """把单条 checklist item 累积到总分/分类/类型统计里。"""

        nonlocal total_items, passed_items
        kind = _normalize_kind(kind)
        if kind == "unknown":
            kind = _normalize_kind(item.get("category") or "unknown")
        cat = str(item.get("category") or "unknown")

        # 新格式：item 里直接有 score/max_score
        # 需求：统计 score/max_score；如果 score 为 null 则跳过（不计入分子与分母）
        score_v = item.get("score")
        max_v = item.get("max_score")
        if str(kind).lower() == "aesthetics" and item.get("llm_score") is not None:
            score_v = item.get("llm_score")
            max_v = 100
        score_i = _to_int_or_none(score_v)
        max_i = _to_int_or_none(max_v)
        if score_v is None:
            # 明确为 null/None：整条跳过
            return

        if score_i is not None and max_i is not None:
            total_items += max_i
            passed_items += score_i
            if max_i > 0:
                score_adj = 0.1 if score_i == 0 else score_i
                item_ratios.append(float(score_adj) / float(max_i))
                item_ratios_by_kind.setdefault(kind, []).append(
                    float(score_adj) / float(max_i)
                )
            by_cat_total[cat] = by_cat_total.get(cat, 0) + max_i
            by_cat_passed[cat] = by_cat_passed.get(cat, 0) + score_i
            by_kind_total[kind] = by_kind_total.get(kind, 0) + max_i
            by_kind_passed[kind] = by_kind_passed.get(kind, 0) + score_i
            return

        # 旧格式兼容：status=pass 计 1 分，否则 0；pending 不计入
        st = _norm_status(item.get("status"))
        if st == "pending":
            return
        total_items += 1
        by_cat_total[cat] = by_cat_total.get(cat, 0) + 1
        by_kind_total[kind] = by_kind_total.get(kind, 0) + 1
        if st == "pass":
            passed_items += 1
            item_ratios.append(1.0)
            item_ratios_by_kind.setdefault(kind, []).append(1.0)
            by_cat_passed[cat] = by_cat_passed.get(cat, 0) + 1
            by_kind_passed[kind] = by_kind_passed.get(kind, 0) + 1
        else:
            # fail 视为 0，但按需求先 +1
            item_ratios.append(1.0)
            item_ratios_by_kind.setdefault(kind, []).append(1.0)

    # 1) 优先读取 merged: checklist.json
    merged_path = os.path.join(task_dir, CHECKLIST_FILE_MERGED)
    merged = _safe_read_json(merged_path)

    # 支持两种 merged 结构：
    # A) 顶层 list: [{..., "category": "Executability"|"Interactivity"|"Aesthetics", ...}, ...]
    # B) 顶层 dict: {"Executability": [...], "Interactivity": [...], "Aesthetics": [...]} 或 {"kinds": {...}}
    if isinstance(merged, list):
        any_items = False
        for it in merged:
            if not isinstance(it, dict):
                continue
            # 合并版里 kind 直接来自 category
            kind = _normalize_kind(it.get("category") or "unknown")
            _accumulate_item(item=it, kind=kind)
            any_items = True
        if any_items:
            found_any = True
    elif isinstance(merged, dict):
        container = merged
        if isinstance(merged.get("kinds"), dict):
            container = merged["kinds"]

        any_items = False
        for kind in ("Executability", "Interactivity", "Aesthetics", "Execution", "Interaction"):
            items = container.get(kind)
            if not isinstance(items, list):
                continue
            for it in items:
                if not isinstance(it, dict):
                    continue
                _accumulate_item(item=it, kind=_normalize_kind(kind))
                any_items = True

        if any_items:
            found_any = True

    # 2) 如果没有 merged，则退回读取三文件（新命名优先，否则 legacy）
    if not found_any:
        checklist_files_to_scan = list(CHECKLIST_FILES)
        if not any(os.path.exists(os.path.join(task_dir, f)) for f in checklist_files_to_scan):
            checklist_files_to_scan = list(CHECKLIST_FILES_LEGACY)

        for fname in checklist_files_to_scan:
            fpath = os.path.join(task_dir, fname)
            data = _safe_read_json(fpath)
            if data is None:
                continue
            kind = _normalize_kind(
                CHECKLIST_KIND_OF_FILE.get(fname, os.path.splitext(fname)[0])
            )
            if not isinstance(data, list):
                # 兼容偶发的非 list 格式
                continue
            found_any = True
            for it in data:
                if not isinstance(it, dict):
                    continue
                _accumulate_item(item=it, kind=kind)

    if not found_any:
        return None

    task_id = os.path.basename(os.path.normpath(task_dir))
    # 调和平均数：直接对所有条目准确率求调和平均数
    hm: Optional[float] = None
    if item_ratios:
        denom = 0.0
        for a in item_ratios:
            if a == 0:
                denom = float("inf")
                break
            denom += 1.0 / float(a)
        hm = 0.0 if denom == float("inf") else float(len(item_ratios)) / denom

    def _harmonic_mean_from_ratios(ratios: List[float]) -> Optional[float]:
        if not ratios:
            return None
        denom = 0.0
        for a in ratios:
            if a == 0:
                denom = float("inf")
                break
            denom += 1.0 / float(a)
        return 0.0 if denom == float("inf") else float(len(ratios)) / denom

    hm_by_kind: Dict[str, Optional[float]] = {}
    for kind, ratios in item_ratios_by_kind.items():
        hm_by_kind[kind] = _harmonic_mean_from_ratios(ratios)

    hm_by_group: Dict[str, Optional[float]] = {}
    hm_by_group["Aesthetics"] = _harmonic_mean_from_ratios(
        item_ratios_by_kind.get("Aesthetics", [])
    )
    hm_by_group["Executability"] = _harmonic_mean_from_ratios(
        item_ratios_by_kind.get("Executability", [])
    )
    hm_by_group["Interactivity"] = _harmonic_mean_from_ratios(
        item_ratios_by_kind.get("Interactivity", [])
    )
    # 兼容别名输出（Execution / Interaction）
    hm_by_group["Execution"] = hm_by_group.get("Executability")
    hm_by_group["Interaction"] = hm_by_group.get("Interactivity")


    score = hm
    max_score = 1.0 if hm is not None else 0.0
    return TaskScore(
        task_id=task_id,
        path=task_dir,
        total_items=total_items,
        passed_items=passed_items,
        score=score,
        max_score=max_score,
        harmonic_mean=hm,
        harmonic_mean_by_kind=hm_by_kind,
        harmonic_mean_by_group=hm_by_group,
        by_category_total=by_cat_total,
        by_category_passed=by_cat_passed,
        by_kind_total=by_kind_total,
        by_kind_passed=by_kind_passed,
    )


def iter_task_dirs(root: str) -> List[str]:
    dirs: List[str] = []
    for name in os.listdir(root):
        p = os.path.join(root, name)
        if not os.path.isdir(p):
            continue
        # 常见题目目录是纯数字；但也可能不是，依靠 checklist 文件判断
        dirs.append(p)
    return sorted(dirs)


def _stable_sort_ids(ids: Sequence[str]) -> List[str]:
    def _k(v: str):
        try:
            return (0, int(v))
        except Exception:
            return (1, v)

    return sorted(list(ids), key=_k)


def select_n_tasks_from_buckets(
    buckets: Dict[str, List[str]],
    n: int,
    *,
    order: Sequence[str] = ("hard", "medium", "easy"),
) -> Dict[str, Any]:
    """从分桶里选满 n 个 task_id。

    规则：按 order 依次取完每个桶，直到凑满 n。
    返回包含 selected_ids 与分桶选取明细。
    """

    if n <= 0:
        return {
            "n": n,
            "selected_ids": [],
            "selected_by_bucket": {k: [] for k in order},
            "counts": {k: 0 for k in order},
            "shortage": 0,
        }

    selected: List[str] = []
    selected_by_bucket: Dict[str, List[str]] = {k: [] for k in order}

    for k in order:
        for tid in buckets.get(k, []):
            if len(selected) >= n:
                break
            selected.append(tid)
            selected_by_bucket[k].append(tid)
        if len(selected) >= n:
            break

    # 去重保险（理论上 buckets 不该重叠）
    deduped: List[str] = []
    seen = set()
    for tid in selected:
        if tid in seen:
            continue
        seen.add(tid)
        deduped.append(tid)

    # 同步 selected_by_bucket
    if len(deduped) != len(selected):
        # 罕见情况：重叠时优先保留先出现的桶
        seen2 = set()
        new_by_bucket: Dict[str, List[str]] = {k: [] for k in order}
        for k in order:
            for tid in selected_by_bucket.get(k, []):
                if tid in seen2:
                    continue
                seen2.add(tid)
                new_by_bucket[k].append(tid)
        selected_by_bucket = new_by_bucket

    shortage = max(0, n - len(deduped))
    return {
        "n": n,
        "selected_ids": deduped,
        "selected_by_bucket": selected_by_bucket,
        "counts": {k: len(selected_by_bucket.get(k, [])) for k in order},
        "shortage": shortage,
    }


def select_n_lowest_tasks(scores: Sequence[TaskScore], n: int) -> Dict[str, Any]:
    """选择分数/准确率最低的 n 个任务。

    排序规则（从“更差”到“更好”）：
    1) max_score <= 0 的任务（无有效分母）最优先被选中（视为最差）
    2) accuracy = score / max_score 越小越优先
    3) accuracy 相同则 max_score 更大者优先（更“有代表性”一些）
    4) 再按 task_id 稳定排序

    返回结构尽量与原 selection_payload 兼容。
    """

    if n <= 0:
        return {
            "n": n,
            "selected_ids": [],
            "selected_by_bucket": {},
            "counts": {},
            "shortage": 0,
            "mode": "lowest",
        }

    def _task_id_key(tid: str):
        try:
            return (0, int(tid))
        except Exception:
            return (1, tid)

    def _sort_key(s: TaskScore):
        if s.max_score <= 0 or s.score is None:
            # 无有效分母/无有效分数：认为最差，放最前
            return (0, 0.0, -s.max_score, _task_id_key(s.task_id))
        acc = float(s.score) / float(s.max_score)
        return (1, float(acc), -int(s.max_score), _task_id_key(s.task_id))

    sorted_scores = sorted(list(scores), key=_sort_key)
    selected = sorted_scores[:n]
    selected_ids = [s.task_id for s in selected]
    shortage = max(0, n - len(selected_ids))

    return {
        "n": n,
        "selected_ids": selected_ids,
        "selected_by_bucket": {"lowest": selected_ids},
        "counts": {"lowest": len(selected_ids)},
        "shortage": shortage,
        "mode": "lowest",
    }


def _accuracy(score: Optional[float], max_score: float) -> Optional[float]:
    if score is None or max_score <= 0:
        return None
    return float(score) / float(max_score)


def _fmt_ratio(score: Any, max_score: Any) -> str:
    try:
        if score is None or max_score is None:
            return ""
        return f"{float(score):.6f}/{float(max_score):.6f}"
    except Exception:
        return ""


def _fmt_acc(acc: Optional[float]) -> str:
    if acc is None:
        return ""
    return f"{acc:.4f}"


def _sum_counts(dicts: Sequence[Dict[str, int]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for d in dicts:
        for k, v in d.items():
            nk = _normalize_kind(k)
            out[nk] = out.get(nk, 0) + int(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="统计 resume_site 下 checklist 得分")
    ap.add_argument(
        "--root",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="resume_site 根目录（默认：脚本所在目录）",
    )
    ap.add_argument(
        "--csv",
        default=None,
        help="输出 CSV 路径（默认：<root>/summary.csv）",
    )
    ap.add_argument(
        "--json",
        dest="json_out",
        default=None,
        help="输出 JSON 路径（默认：<root>/summary.json）",
    )
    ap.add_argument(
        "--select",
        type=int,
        default=100,
        help="额外输出抽取的题目列表：抽满 N 道题（默认：100；<=0 则不输出）",
    )
    ap.add_argument(
        "--select-prefix",
        default=None,
        help=(
            "抽题输出文件名前缀（默认：<root>/selected_<N>）；"
            "会生成 .txt/.json/.csv"
        ),
    )
    ap.add_argument(
        "--task-ids",
        default=None,
        help=(
            "只统计/输出指定 task_id（逗号或空格分隔）。"
            "例如：--task-ids '216,946,985'"
        ),
    )
    ap.add_argument(
        "--task-ids-file",
        default=None,
        help=(
            "从文件读取 task_id 列表（支持：一行一个 / 逗号分隔 / 空格分隔）。"
            "与 --task-ids 合并后去重。"
        ),
    )
    ap.add_argument(
        "--debug",
        action="store_true",
        help="打印调试信息（脚本路径、kind 原始/归一化统计）",
    )
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    out_csv = os.path.abspath(args.csv or os.path.join(root, "summary.csv"))
    out_json = os.path.abspath(args.json_out or os.path.join(root, "summary.json"))

    def _parse_task_ids(text: str) -> List[str]:
        ids: List[str] = []
        if not text:
            return ids
        for chunk in re.split(r"[\s,]+", text.strip()):
            c = chunk.strip()
            if not c:
                continue
            ids.append(str(c))
        return ids

    # 可选：只处理指定的题号
    filter_ids: Optional[set[str]] = None
    wanted: List[str] = []
    if args.task_ids:
        wanted.extend(_parse_task_ids(str(args.task_ids)))
    if args.task_ids_file:
        try:
            with open(str(args.task_ids_file), "r", encoding="utf-8") as f:
                wanted.extend(_parse_task_ids(f.read()))
        except FileNotFoundError:
            raise SystemExit(f"task ids file not found: {args.task_ids_file}")
    if wanted:
        filter_ids = set(wanted)

    scores: List[TaskScore] = []
    for d in iter_task_dirs(root):
        if filter_ids is not None:
            tid = os.path.basename(os.path.normpath(d))
            if tid not in filter_ids:
                continue
        s = score_one_task_dir(d)
        if s is not None:
            scores.append(s)

    # 汇总：所有题的调和均值平均数
    valid_scores = [s.score for s in scores if s.score is not None]
    total_avg = (sum(valid_scores) / len(valid_scores)) if valid_scores else None

    # 控制台输出（按 task_id 排序）
    def _key(x: TaskScore):
        try:
            return int(x.task_id)
        except Exception:
            return x.task_id

    scores_sorted = sorted(scores, key=_key)

    if args.debug:
        print("-" * 40)
        print(f"[DEBUG] script={os.path.abspath(__file__)}")
        print(f"[DEBUG] root={root}")
        raw_kind_totals: Dict[str, int] = {}
        norm_kind_totals: Dict[str, int] = {}
        for s in scores_sorted:
            for k, v in s.by_kind_total.items():
                raw_kind_totals[k] = raw_kind_totals.get(k, 0) + int(v)
                nk = _normalize_kind(k)
                norm_kind_totals[nk] = norm_kind_totals.get(nk, 0) + int(v)
        print(f"[DEBUG] raw_kind_totals={json.dumps(raw_kind_totals, ensure_ascii=False)}")
        print(f"[DEBUG] norm_kind_totals={json.dumps(norm_kind_totals, ensure_ascii=False)}")
    for s in scores_sorted:
        score_s = "" if s.score is None else f"{s.score:.6f}"
        print(f"{s.task_id}\t{score_s}\t(hmean)\t(passed={s.passed_items}, total={s.total_items})")

        # 每题按类别打印（只打印该题出现过的类别）
        cats = sorted(set(s.by_category_total.keys()) | set(s.by_category_passed.keys()))
        for cat in cats:
            p = s.by_category_passed.get(cat, 0)
            t = s.by_category_total.get(cat, 0)
            print(f"  - {cat}: {p}/{t}")

        # 每题按 checklist 类型(aesthetics/execution/interaction)打印
        kinds = sorted(set(s.by_kind_total.keys()) | set(s.by_kind_passed.keys()))
        for k in kinds:
            p = s.by_kind_passed.get(k, 0)
            t = s.by_kind_total.get(k, 0)
            print(f"  * {k}: {p}/{t}")

    print("-" * 40)
    if total_avg is None:
        print(f"TOTAL_AVG\t\t(tasks={len(scores_sorted)})")
    else:
        print(f"TOTAL_AVG\t{total_avg:.6f}\t(tasks={len(scores_sorted)})")

    if filter_ids is not None:
        miss = [tid for tid in _stable_sort_ids(list(filter_ids)) if tid not in {s.task_id for s in scores_sorted}]
        if miss:
            print("-" * 40)
            print(f"[Warn] {len(miss)} task_id(s) not found or no checklist in root: " + ",".join(miss))

    # 按准确率分档：<=1/2 困难，<=2/3 中等，其余简单
    buckets: Dict[str, List[str]] = {
        "hard": [],
        "medium": [],
        "easy": [],
        "no_items": [],
    }
    for s in scores_sorted:
        if s.max_score <= 0:
            buckets["no_items"].append(s.task_id)
            continue
        acc = _accuracy(s.score, s.max_score)
        if acc is None:
            buckets["no_items"].append(s.task_id)
            continue
        if acc <= 1 / 100:
            buckets["hard"].append(s.task_id)
        elif acc <= 1 / 2:
            buckets["medium"].append(s.task_id)
        else:
            buckets["easy"].append(s.task_id)

    for k in list(buckets.keys()):
        buckets[k] = _stable_sort_ids(buckets[k])

    print("-" * 40)
    print("DIFFICULTY_BUCKETS (by accuracy)")
    print(f"hard   (<=1/2): {len(buckets['hard'])}\t" + ",".join(buckets["hard"]))
    print(f"medium (<=2/3): {len(buckets['medium'])}\t" + ",".join(buckets["medium"]))
    print(f"easy    (>2/3): {len(buckets['easy'])}\t" + ",".join(buckets["easy"]))
    if buckets["no_items"]:
        print(f"no_items: {len(buckets['no_items'])}\t" + ",".join(buckets["no_items"]))

    # 全局按类别汇总打印
    global_total: Dict[str, int] = {}
    global_passed: Dict[str, int] = {}
    for s in scores_sorted:
        for cat, t in s.by_category_total.items():
            global_total[cat] = global_total.get(cat, 0) + int(t)
        for cat, p in s.by_category_passed.items():
            global_passed[cat] = global_passed.get(cat, 0) + int(p)

    all_cats = sorted(set(global_total.keys()) | set(global_passed.keys()))
    for cat in all_cats:
        p = global_passed.get(cat, 0)
        t = global_total.get(cat, 0)
        print(f"TOTAL[{cat}]\t{p}/{t}")

    # 全局按 checklist 类型汇总打印
    global_kind_total = _sum_counts([s.by_kind_total for s in scores_sorted])
    global_kind_passed = _sum_counts([s.by_kind_passed for s in scores_sorted])
    print("-" * 40)
    print("TOTAL_BY_KIND")
    for k in ("Executability", "Interactivity", "Aesthetics"):
        p = global_kind_passed.get(k, 0)
        t = global_kind_total.get(k, 0)
        print(f"TOTAL_KIND[{k}]\t{p}/{t}")

    # 每类调和平均数的平均值（按题目均值，仅统计该类有有效分数的题）
    mean_hm_by_kind: Dict[str, Optional[float]] = {}
    for k in ("Executability", "Interactivity", "Aesthetics"):
        vals: List[float] = []
        for s in scores_sorted:
            for kk, vv in s.harmonic_mean_by_kind.items():
                if _normalize_kind(kk) == k and isinstance(vv, (int, float)):
                    vals.append(float(vv))
        mean_hm_by_kind[k] = (sum(vals) / len(vals)) if vals else None

    print("-" * 40)
    print("MEAN_HARMONIC_BY_KIND")
    for k in ("Executability", "Interactivity", "Aesthetics"):
        v = mean_hm_by_kind.get(k)
        if v is None:
            print(f"HMEAN_AVG[{k}]\t")
        else:
            print(f"HMEAN_AVG[{k}]\t{v:.6f}")

    # 美学 / 执行 / 交互 各自计算
    mean_hm_by_group: Dict[str, Optional[float]] = {}
    for g in ("Aesthetics", "Executability", "Interactivity", "Execution", "Interaction"):
        vals = [s.harmonic_mean_by_group.get(g) for s in scores_sorted]
        vals = [v for v in vals if isinstance(v, (int, float))]
        mean_hm_by_group[g] = (sum(vals) / len(vals)) if vals else None

    print("-" * 40)
    print("MEAN_HARMONIC_BY_GROUP")
    for g in ("Aesthetics", "Execution", "Interaction"):
        v = mean_hm_by_group.get(g)
        if v is None:
            print(f"HMEAN_AVG_GROUP[{g}]\t")
        else:
            print(f"HMEAN_AVG_GROUP[{g}]\t{v:.6f}")

    # 抽取 N 道题：选择整体分数(accuracy)最低的 N 道
    selection_payload: Optional[Dict[str, Any]] = None
    if int(args.select) > 0:
        selection_payload = select_n_lowest_tasks(scores_sorted, int(args.select))
        selected_ids: List[str] = selection_payload["selected_ids"]
        print("-" * 40)
        print(
            f"SELECTED_TASKS n={selection_payload['n']} (mode=lowest accuracy) "
            f"selected={len(selected_ids)} shortage={selection_payload['shortage']}"
        )

        ids = selection_payload.get("selected_by_bucket", {}).get("lowest", [])
        if ids:
            print(f"lowest: {len(ids)}\t" + ",".join(ids))

        # 写出 selected 文件
        prefix = args.select_prefix or os.path.join(root, f"selected_{int(args.select)}")
        prefix = os.path.abspath(prefix)
        out_sel_txt = prefix + ".txt"
        out_sel_json = prefix + ".json"
        out_sel_csv = prefix + ".csv"

        # 额外附上每题分数，方便你后续筛/抽样
        score_map: Dict[str, TaskScore] = {s.task_id: s for s in scores_sorted}

        # task_id -> bucket（为了兼容输出格式；最低分模式统一标为 lowest）
        bucket_of: Dict[str, str] = {}
        for tid in selected_ids:
            bucket_of[tid] = "lowest"

        # 精简版行（用于 txt/csv/json 的 tasks 列表）
        selected_rows: List[Dict[str, Any]] = []
        for tid in selected_ids:
            s = score_map.get(tid)
            b = bucket_of.get(tid, "")
            if s is None:
                selected_rows.append({
                    "task_id": tid,
                    "bucket": b,
                    "score": None,
                    "max_score": None,
                    "accuracy": None,
                    "path": None,
                })
            else:
                selected_rows.append({
                    "task_id": s.task_id,
                    "bucket": b,
                    "score": s.score,
                    "max_score": s.max_score,
                    "accuracy": _accuracy(s.score, s.max_score),
                    "path": s.path,
                    "passed_items": s.passed_items,
                    "total_items": s.total_items,
                    "by_kind_passed": s.by_kind_passed,
                    "by_kind_total": s.by_kind_total,
                })

        # TXT：一行一个 task，带分数信息，方便肉眼/grep
        os.makedirs(os.path.dirname(out_sel_txt) or root, exist_ok=True)
        with open(out_sel_txt, "w", encoding="utf-8") as f:
            f.write("task_id\tbucket\tscore\tmax_score\taccuracy\tpath\n")
            for row in selected_rows:
                acc = row.get("accuracy")
                acc_s = "" if acc is None else f"{acc:.4f}"
                f.write(
                    f"{row.get('task_id','')}\t{row.get('bucket','')}\t"
                    f"{row.get('score','')}\t{row.get('max_score','')}\t{acc_s}\t"
                    f"{row.get('path','')}\n"
                )

        # selection 统计：整体分数与各桶汇总
        sel_total_score = 0
        sel_total_max = 0
        sel_by_bucket: Dict[str, Dict[str, Any]] = {}
        for row in selected_rows:
            b = str(row.get("bucket") or "")
            if b not in sel_by_bucket:
                sel_by_bucket[b] = {"count": 0, "score": 0, "max_score": 0}
            sel_by_bucket[b]["count"] += 1
            if isinstance(row.get("score"), (int, float)) and isinstance(row.get("max_score"), (int, float)):
                sel_by_bucket[b]["score"] += float(row["score"])
                sel_by_bucket[b]["max_score"] += float(row["max_score"])
                sel_total_score += float(row["score"])
                sel_total_max += float(row["max_score"])

        sel_stats = {
            "selected_count": len(selected_rows),
            "selected_total_score": sel_total_score,
            "selected_total_max_score": sel_total_max,
            "selected_accuracy": _accuracy(sel_total_score, sel_total_max),
            "selected_by_bucket": sel_by_bucket,
        }

        # selected 按 checklist 类型汇总
        selected_kind_total: Dict[str, int] = {}
        selected_kind_passed: Dict[str, int] = {}
        for row in selected_rows:
            kt = row.get("by_kind_total")
            kp = row.get("by_kind_passed")
            if isinstance(kt, dict):
                for k, v in kt.items():
                    nk = _normalize_kind(k)
                    selected_kind_total[nk] = selected_kind_total.get(nk, 0) + int(v)
            if isinstance(kp, dict):
                for k, v in kp.items():
                    nk = _normalize_kind(k)
                    selected_kind_passed[nk] = selected_kind_passed.get(nk, 0) + int(v)

        sel_stats["selected_by_kind"] = {
            "passed": selected_kind_passed,
            "total": selected_kind_total,
            "accuracy": {
                k: _accuracy(selected_kind_passed.get(k, 0), selected_kind_total.get(k, 0))
                for k in sorted(set(selected_kind_total.keys()) | set(selected_kind_passed.keys()))
            },
        }

        # 补齐每个 bucket 的 accuracy（便于你后续从 JSON 里直接取）
        for b, v in sel_by_bucket.items():
            try:
                v["accuracy"] = _accuracy(float(v.get("score", 0.0)), float(v.get("max_score", 0.0)))
            except Exception:
                v["accuracy"] = None

        # 控制台打印 selected 的分桶得分/准确率（lowest 单桶）
        print("-" * 40)
        print("SELECTED_BUCKET_SCORES")
        ordered_buckets = ["lowest"] + [b for b in sorted(sel_by_bucket.keys()) if b != "lowest"]
        for b in ordered_buckets:
            v = sel_by_bucket.get(b)
            if not v:
                continue
            s = v.get("score", 0.0)
            m = v.get("max_score", 0.0)
            a = v.get("accuracy")
            c = v.get("count", 0)
            print(
                f"selected[{b}]\t{_fmt_ratio(s, m)}\tacc={_fmt_acc(a)}\tcount={c}"
            )

        print("-" * 40)
        print("SELECTED_KIND_SCORES")
        for k in ("Executability", "Interactivity", "Aesthetics"):
            p = selected_kind_passed.get(k, 0)
            t = selected_kind_total.get(k, 0)
            print(f"selected_kind[{k}]\t{p}/{t}\tacc={_fmt_acc(_accuracy(p, t))}")

        sel_payload_full = {
            "root": root,
            "selection": selection_payload,
            "selection_stats": sel_stats,
            "tasks": selected_rows,
        }
        with open(out_sel_json, "w", encoding="utf-8") as f:
            json.dump(sel_payload_full, f, ensure_ascii=False, indent=2)

        with open(out_sel_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "task_id",
                "bucket",
                "score",
                "max_score",
                "accuracy",
                "passed_items",
                "total_items",
                "path",
                "by_kind_passed",
                "by_kind_total",
            ])

            for row in selected_rows:
                w.writerow([
                    row.get("task_id", ""),
                    row.get("bucket", ""),
                    "" if row.get("score") is None else f"{float(row.get('score')):.6f}",
                    "" if row.get("max_score") is None else f"{float(row.get('max_score')):.6f}",
                    "" if row.get("accuracy") is None else f"{row.get('accuracy'):.6f}",
                    row.get("passed_items", ""),
                    row.get("total_items", ""),
                    row.get("path", ""),
                    json.dumps(row.get("by_kind_passed", {}), ensure_ascii=False),
                    json.dumps(row.get("by_kind_total", {}), ensure_ascii=False),
                ])

        print(f"[written] {out_sel_txt}")
        print(f"[written] {out_sel_json}")
        print(f"[written] {out_sel_csv}")

    # 写 CSV
    os.makedirs(os.path.dirname(out_csv) or root, exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "task_id",
            "score",
            "max_score",
            "passed_items",
            "total_items",
            "path",
            "by_category_passed",
            "by_category_total",
        ])
        for s in scores_sorted:
            w.writerow([
                s.task_id,
                s.score,
                s.max_score,
                s.passed_items,
                s.total_items,
                s.path,
                json.dumps(s.by_category_passed, ensure_ascii=False),
                json.dumps(s.by_category_total, ensure_ascii=False),
            ])
        w.writerow([
            "TOTAL_AVG",
            "" if total_avg is None else f"{total_avg:.6f}",
            "",
            "",
            "",
            root,
            "",
            "",
        ])

    # 写 JSON
    os.makedirs(os.path.dirname(out_json) or root, exist_ok=True)
    payload = {
        "root": root,
        "total_avg_score": total_avg,
        "mean_harmonic_by_kind": mean_hm_by_kind,
        "mean_harmonic_by_group": mean_hm_by_group,
        "by_category_passed": global_passed,
        "by_category_total": global_total,
        "by_kind_passed": global_kind_passed,
        "by_kind_total": global_kind_total,
        "difficulty_buckets": {
            "rules": {
                "hard": "accuracy <= 1/2",
                "medium": "accuracy <= 2/3",
                "easy": "accuracy > 2/3",
                "pending_ignored": True,
            },
            "counts": {
                "hard": len(buckets["hard"]),
                "medium": len(buckets["medium"]),
                "easy": len(buckets["easy"]),
                "no_items": len(buckets["no_items"]),
            },
            "task_ids": buckets,
        },
        "selection": selection_payload,
        "tasks": [asdict(s) for s in scores_sorted],
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[written] {out_csv}")
    print(f"[written] {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# Claude-Opus-4.5
# Gemini-3-Pro
# Gemini-3-Flash
# GLM-4.7
# Claude-4.5-Sonnet
# Qwen3-Coder-480B
# Qwen3-VL-30B-A3B-Instruct
# Qwen3-VL-32B-Instruct
# MiniMax-M2.1
# GPT-5.2
# Deepseek-V3.2
# Qwen3-VL-235B-A22B-Instruct
# Qwen3-8B
# Qwen3-32B
# 

# python /share/leixinping/Test/calculate_tiaohe_for_image.py \
#   --root /share/leixinping/Test/image_bench_v1/Qwen3-VL-235B-A22B-Instruct/resume_site \
#   --select 0 \
#   --debug \
#   --task-ids "4,5,8,10,12,21,23,26,27,31,37,39,40,45,51,56,61,70,72,73,76,78,84,85,90,101,106,107,114,117,118,127,131,133,146,147,6,25,58,62,93,125,137,3,17,28,29,38,42,49,59,60,64,109,121"

# python /share/leixinping/Test/calculate_tiaohe_for_image.py \
#   --root /share/leixinping/Test/image_bench_v1/GPT-5.2/resume_site \
#   --select 0 \
#   --debug \
#   --task-ids "1, 2, 5, 7, 8, 15, 17, 18, 22, 24, 28, 29, 30, 32, 33, 36, 38, 40, 43, 49, 50, 52, 55, 57, 58, 59, 60, 62, 64"

