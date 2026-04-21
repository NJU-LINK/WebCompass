"""UI 复刻评审脚本。

输入：包含多个网页 repo 的根目录（每个 repo 内有 checklist.json）。
输出：每个 repo 生成 llm_judge.json，并可选生成汇总文件。
"""

from __future__ import annotations
import sys
import os

# Add parent paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

try:
    from generation.call_model import call_api
except ImportError:
    from call_model import call_api


judge_prompt = """
你现在是一名专业的网页 UI 复刻评审专家，专注于评估大模型或开发者的 UI 还原能力。你的核心任务是：对比【原网页 UI 设计图】和【复刻实现图】，采用 **“基础分 + 细节扣减”** 的分层加权机制进行评分。该机制旨在先肯定核心框架的还原成果，再通过细节差异拉开分数档次，确保评分既有区分度，又客观公平。
评分体系（总分 100 分）
评分分为两个阶段，严格按照以下权重和规则执行：
第一阶段：核心基础分（保底权重 30%）
分值：固定初始分 30 分。
评审内容：仅评估宏观结构与核心识别度。布局结构：页面整体排版、元素的相对位置、主次层级关系是否与原图一致。
核心元素：关键按钮、标题文字、核心图形（如 Logo、主图标）是否存在且形态正确。
风格调性：整体色彩风格、质感（扁平 / 拟物）是否与原图相符。
阶段判定：若核心框架完全正确，基础分全额保留（30 分），进入第二阶段。
若核心框架存在重大错误（如布局错乱、核心按钮缺失、主视觉完全不符），直接判定为复刻失败，基础分归零（0 分），无需进入第二阶段，最终得分即为 0 分。
第二阶段：细节扣减分（区分权重 70%）
分值：在 30 分基础上，拥有70 分的细节容错空间。
评审内容：在核心框架正确的前提下，校验所有肉眼可见的细节。
扣减规则（累加扣减，扣完 70 分为止）：中度差异（-15 分 / 处）：颜色色值明显偏差、字号 / 字重差异较大、按钮形状 / 圆角不符、装饰元素位置偏移。
轻度差异（-10 分 / 处）：文字行高细微偏差、间距（Margin/Padding）像素级误差、阴影 / 渐变效果不完全一致、非核心装饰样式细微不同。
极微差异（-1 分 / 处）：字体渲染的轻微锯齿、因截图压缩导致的不可避免的色差。

请列出所有评审细节，并按照以下格式输出最后的分数：

```json
{
    "score": <final score>
}
```
"""


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
FILENAME_PATTERN = re.compile(r"([\w\- ./()]+\.(?:png|jpg|jpeg|webp))", re.IGNORECASE)


@dataclass
class JudgeResult:
    repo: str
    task: str
    reference_image: Optional[str]
    webpage_image: Optional[str]
    score: Optional[int]
    raw_response: Optional[str]
    model: str
    model_group: Optional[str] = None
    error: Optional[str] = None


def _list_images(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []
    return [f for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTENSIONS)]


def _normalize_candidate(candidate: str) -> str:
    return candidate.strip().strip('"').strip("'")


def _resolve_candidate(repo_path: str, candidate: str, search_dirs: Sequence[str]) -> Optional[str]:
    candidate = _normalize_candidate(candidate)
    if not candidate:
        return None

    if os.path.isabs(candidate) and os.path.isfile(candidate):
        return candidate

    direct = os.path.join(repo_path, candidate)
    if os.path.isfile(direct):
        return direct

    for folder in search_dirs:
        path = os.path.join(repo_path, folder, candidate)
        if os.path.isfile(path):
            return path
    return None


def _extract_filenames_from_text(text: str) -> List[str]:
    if not text:
        return []
    return [_normalize_candidate(m.group(1)) for m in FILENAME_PATTERN.finditer(text)]


def _gather_text_fields(entry: dict) -> str:
    fields = []
    for key, value in entry.items():
        if isinstance(value, str):
            fields.append(value)
    return "\n".join(fields)


def _pick_existing_filename(candidates: Iterable[str], folder: str) -> Optional[str]:
    if not os.path.isdir(folder):
        return None
    existing = set(os.listdir(folder))
    for candidate in candidates:
        if candidate in existing:
            return candidate
    return None


def _resolve_images(entry: dict, repo_path: str) -> tuple[Optional[str], Optional[str]]:
    screenshots_dir = os.path.join(repo_path, "screenshots")
    image_dir = os.path.join(repo_path, "image")

    reference_name = entry.get("reference_image_path")
    webpage_name = entry.get("webpage_screenshot_path")

    text_blob = _gather_text_fields(entry)
    text_candidates = _extract_filenames_from_text(text_blob)

    if not reference_name:
        reference_name = _pick_existing_filename(text_candidates, screenshots_dir)
    if not webpage_name:
        webpage_name = _pick_existing_filename(text_candidates, image_dir)

    reference_path = None
    if reference_name:
        if not os.path.isabs(reference_name) and os.path.basename(reference_name) == reference_name:
            candidate = os.path.join(screenshots_dir, reference_name)
            if os.path.isfile(candidate):
                reference_path = candidate
        if reference_path is None:
            reference_path = _resolve_candidate(repo_path, reference_name, ["screenshots", "image"])

    webpage_path = None
    if webpage_name:
        if not os.path.isabs(webpage_name) and os.path.basename(webpage_name) == webpage_name:
            candidate = os.path.join(image_dir, webpage_name)
            if os.path.isfile(candidate):
                webpage_path = candidate
        if webpage_path is None:
            webpage_path = _resolve_candidate(repo_path, webpage_name, ["image", "screenshots"])

    if reference_path is None:
        candidates = _list_images(screenshots_dir)
        if len(candidates) == 1:
            reference_path = os.path.join(screenshots_dir, candidates[0])

    if webpage_path is None:
        candidates = _list_images(image_dir)
        if len(candidates) == 1:
            webpage_path = os.path.join(image_dir, candidates[0])

    return reference_path, webpage_path


def _extract_score(raw_text: str) -> Optional[int]:
    if not raw_text:
        return None

    try:
        json_match = re.search(r"\{.*?\}", raw_text, re.DOTALL)
        if json_match:
            payload = json.loads(json_match.group(0))
            score = payload.get("score")
            if isinstance(score, (int, float)):
                return int(round(score))
    except Exception:
        pass

    match = re.search(r"score\s*[:=]\s*(\d+)", raw_text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def _load_checklist(path: str) -> Optional[List[dict]]:
    """加载 checklist.json，解析失败时返回 None 而非抛异常。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            print(f"⚠️ checklist.json 为空，跳过: {path}")
            return None
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        print(f"⚠️ checklist.json 格式不正确（非数组），跳过: {path}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ checklist.json 解析失败，跳过: {path}\n   错误详情: {e}")
        return None
    except Exception as e:
        print(f"⚠️ 读取 checklist.json 出错，跳过: {path}\n   错误详情: {e}")
        return None



def _iter_repos(root_dir: str, target_subdir: str = "resume_site") -> Iterable[str]:
    target_root = os.path.join(root_dir, target_subdir)
    if not os.path.isdir(target_root):
        return
    for dirpath, _, filenames in os.walk(target_root):
        if "checklist.json" in filenames:
            yield dirpath


def _write_checklist(path: str, checklist: List[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checklist, f, ensure_ascii=False, indent=2)


def _format_result(result: JudgeResult) -> dict:
    return {
        "repo": result.repo,
        "model_group": result.model_group,
        "task": result.task,
        "score": result.score,
        "reference_image": result.reference_image,
        "webpage_image": result.webpage_image,
        "model": result.model,
        "error": result.error,
        "raw_response": result.raw_response,
    }

def judge_repo(
    repo_path: str,
    model: str,
    stream: bool = False,
    max_workers: int = 4,
    model_group: Optional[str] = None,
) -> List[JudgeResult]:
    checklist_path = os.path.join(repo_path, "checklist.json")
    checklist = _load_checklist(checklist_path)

    # ========== 新增：加载失败直接返回空结果 ==========
    if checklist is None:
        print(f"⚠️ 跳过仓库（checklist 无法加载）: {repo_path}")
        return []
    # ================================================

    results: List[JudgeResult] = []

    if stream and max_workers > 1:
        print("提示：stream 模式下将禁用并发，避免输出混乱。")
        max_workers = 1

    def _is_already_judged(entry: dict) -> bool:
        return (
            entry.get("llm_judge_model") is not None
            or entry.get("llm_score") is not None
            or entry.get("llm_judge_error") is not None
        )

    def process_entry(entry: dict) -> Optional[JudgeResult]:
        if entry.get("category") != "Aesthetics":
            return None
        if _is_already_judged(entry):
            return None

        task = entry.get("task", "(unknown task)")
        print(f"  - 正在处理: {task}")
        reference_path, webpage_path = _resolve_images(entry, repo_path)

        if not reference_path or not webpage_path:
            entry["llm_score"] = None
            entry["llm_judge_error"] = "未能解析到完整的原图或复刻图路径"
            entry["llm_judge_model"] = model
            return JudgeResult(
                repo=os.path.basename(repo_path),
                task=task,
                reference_image=reference_path,
                webpage_image=webpage_path,
                score=None,
                raw_response=None,
                model=model,
                model_group=model_group,
                error="未能解析到完整的原图或复刻图路径",
            )

        try:
            raw = call_api(
                judge_prompt,
                model=model,
                image_path=[reference_path, webpage_path],
                stream_print=stream,
            )
            score = _extract_score(raw)
            entry["llm_score"] = score
            entry["llm_judge_model"] = model
            entry["llm_judge_error"] = None
            return JudgeResult(
                repo=os.path.basename(repo_path),
                task=task,
                reference_image=reference_path,
                webpage_image=webpage_path,
                score=score,
                raw_response=raw,
                model=model,
                model_group=model_group,
            )
        except Exception as exc:
            entry["llm_score"] = None
            entry["llm_judge_model"] = model
            entry["llm_judge_error"] = str(exc)
            return JudgeResult(
                repo=os.path.basename(repo_path),
                task=task,
                reference_image=reference_path,
                webpage_image=webpage_path,
                score=None,
                raw_response=None,
                model=model,
                model_group=model_group,
                error=str(exc),
            )

    total_aesthetics = sum(1 for entry in checklist if entry.get("category") == "Aesthetics")
    skipped_aesthetics = sum(
        1
        for entry in checklist
        if entry.get("category") == "Aesthetics" and _is_already_judged(entry)
    )
    tasks = [
        entry
        for entry in checklist
        if entry.get("category") == "Aesthetics" and not _is_already_judged(entry)
    ]
    print(
        f"开始评审: {os.path.basename(repo_path)} | Aesthetics={total_aesthetics} | "
        f"已跳过={skipped_aesthetics} | 待处理={len(tasks)}"
    )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_entry, entry) for entry in tasks]
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    _write_checklist(checklist_path, checklist)
    return results


def _write_repo_results(repo_path: str, results: List[JudgeResult]) -> str:
    output_path = os.path.join(repo_path, "llm_judge.json")
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "results": [_format_result(result) for result in results],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return output_path


def _write_summary(path: str, results: List[JudgeResult]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(_format_result(result), ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="UI 复刻评审：批量读取 checklist.json 并调用模型打分")
    parser.add_argument("root", help="包含多个模型目录的根目录")
    parser.add_argument("--models", nargs="+", required=True, help="模型目录名列表（每个目录下包含网页文件夹）")
    parser.add_argument("--model", default="claude-opus-4-5-20250929", help="使用的多模态模型名称")
    parser.add_argument("--stream", action="store_true", help="是否流式打印模型输出")
    parser.add_argument("--max-workers", type=int, default=4, help="并发线程数")
    parser.add_argument("--summary", default=None, help="输出汇总 jsonl 文件路径")

    args = parser.parse_args()
    root_dir = os.path.abspath(args.root)

    all_results: List[JudgeResult] = []
    for model_group in args.models:
        model_root = os.path.join(root_dir, model_group)
        if not os.path.isdir(model_root):
            print(f"警告：模型目录不存在，已跳过：{model_root}")
            continue
        for repo_path in _iter_repos(model_root, target_subdir="resume_site"):
            try:
                results = judge_repo(
                    repo_path,
                    model=args.model,
                    stream=args.stream,
                    max_workers=args.max_workers,
                    model_group=model_group,
                )
                if results:
                    _write_repo_results(repo_path, results)
                    all_results.extend(results)
            except Exception as e:
                print(f"⚠️ 处理仓库时发生未预期错误，跳过: {repo_path}\n   错误详情: {e}")
                continue

    if args.summary:
        _write_summary(os.path.abspath(args.summary), all_results)

    print(f"完成评审：共处理 {len(all_results)} 条美学任务")


if __name__ == "__main__":
    main()

# python /share/leixinping/Test/judge_image.py \
#   /share/leixinping/Test/image_bench_haiku/ \
#   --models Gemini-3-Pro \
#   --model Gemini-3-Flash \
#   --max-workers 10 \
#   --summary /share/leixinping/data/image_bench/final_test/summary.jsonl


# for i in 2 3 4; do
#     python3 /share/leixinping/data/image_bench/gen_web_from_image.py \
#       --checklist_jsonl /share/leixinping/data/image_bench/data/output_revised/checklist_sub.jsonl \
#       --images_root /share/leixinping/data/image_bench/data/output \
#       --repos_folder /share/leixinping/data/image_bench/pass${i}_qwen \
#       --models Qwen3-VL-235B-A22B-Instruct \
#       --max_workers 5 \
#       --max_images -1
# done