import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from tqdm import tqdm
import json
import argparse

from llm.judge.code_judge import CodeJudge
from llm.judge.prompt import (
    EDIT_JUDGE_SYSTEM_PROMPT,
    REPAIR_JUDGE_SYSTEM_PROMPT,
)


def get_generated_folders(
    results_path: str, output_filename: str = "judge.json"
) -> List[Dict[str, str]]:
    """列出 results_path 下所有待评分的 case 目录。

    results_path 直接包含 <id>/ 子目录 (e.g. results/edit/<session>/sp/)。
    """
    task_path = Path(results_path)
    if not task_path.exists():
        print(f"Warning: results path not found: {task_path}")
        return []

    folders = []
    for folder in task_path.iterdir():
        if folder.is_dir():
            # 检查是否已有评分结果
            judge_file = folder / output_filename
            if judge_file.exists():
                print(f"Skipping {folder.name} (already judged)")
                continue

            # 检查是否有 info.json
            info_file = folder / "info.json"
            if not info_file.exists():
                print(f"Warning: {folder.name} missing info.json")
                continue

            folders.append(
                {"generated_folder": str(folder), "folder_name": folder.name}
            )

    return folders


def find_data_folder(base_data_path: str, folder_name: str) -> str:
    """根据 case 名查找对应的原始数据文件夹 (base_data_path 已指向 leaf 层)。"""
    data_folder = Path(base_data_path) / folder_name
    if not data_folder.exists():
        raise FileNotFoundError(f"Data folder not found: {data_folder}")
    return str(data_folder)


def process_single_judge(
    data_folder: str,
    generated_folder: str,
    judge: CodeJudge,
    task_type: str,
    output_filename: str = "judge.json",
) -> Dict[str, Any]:
    """处理单个评分任务"""
    try:
        result = judge.judge_task(
            data_folder=data_folder,
            generated_folder=generated_folder,
            task=task_type,
            output_filename=output_filename,
        )

        return {
            "folder": generated_folder,
            "task_type": task_type,
            "status": "success",
            "judge_result": result.get("judge_result", {}),
        }
    except Exception as e:
        import traceback

        return {
            "folder": generated_folder,
            "task_type": task_type,
            "status": "failed",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def judge_single_task_type(
    base_data_path: str,
    results_path: str,
    task_type: str,
    judge: CodeJudge,
    max_workers: int = 4,
    output_filename: str = "judge.json",
) -> Dict[str, Any]:
    """并行评分单个任务类型的所有生成结果

    Args:
        base_data_path: 原始数据集路径
        results_path: 生成结果路径
        task_type: 任务类型 (edit/repair)
        judge: CodeJudge 实例
        max_workers: 最大线程数
        output_filename: 评分结果文件名 (默认: judge.json)

    Returns:
        包含结果和统计的字典
    """
    print(f"\n{'='*60}")
    print(f"Judging {task_type.upper()} tasks")
    print(f"{'='*60}")

    # 获取所有待评分的文件夹
    folders = get_generated_folders(results_path, output_filename)
    total = len(folders)

    if total == 0:
        print(f"No {task_type} tasks to judge")
        return {
            "task_type": task_type,
            "total": 0,
            "success": 0,
            "failed": 0,
            "results": [],
        }

    print(f"Found {total} {task_type} tasks to judge\n")

    results = []
    success_count = 0
    failed_count = 0

    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_folder = {}
        for folder_info in folders:
            try:
                data_folder = find_data_folder(
                    base_data_path, folder_info["folder_name"]
                )

                future = executor.submit(
                    process_single_judge,
                    data_folder,
                    folder_info["generated_folder"],
                    judge,
                    task_type,
                    output_filename,
                )
                future_to_folder[future] = folder_info["generated_folder"]
            except FileNotFoundError as e:
                print(f"Warning: {e}")
                failed_count += 1
                results.append(
                    {
                        "folder": folder_info["generated_folder"],
                        "task_type": task_type,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        # 使用tqdm显示进度
        with tqdm(
            total=len(future_to_folder), desc=f"{task_type.capitalize()}"
        ) as pbar:
            for future in as_completed(future_to_folder):
                result = future.result()
                results.append(result)

                if result["status"] == "success":
                    success_count += 1
                else:
                    failed_count += 1
                    print(f"\n❌ Failed: {Path(result['folder']).name}")
                    print(f"   Error: {result['error']}")

                pbar.update(1)
                pbar.set_postfix(success=success_count, failed=failed_count)

    # 输出统计
    success_rate = (success_count / total * 100) if total > 0 else 0
    print(f"\n{task_type.upper()} Summary:")
    print(f"  Total: {total}")
    print(f"  Success: {success_count} ({success_rate:.2f}%)")
    print(f"  Failed: {failed_count}")

    return {
        "task_type": task_type,
        "total": total,
        "success": success_count,
        "failed": failed_count,
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch judge runner")
    parser.add_argument("--base-data-path", required=True, help="原始数据集根目录")
    parser.add_argument("--results-path", required=True, help="生成结果路径")
    parser.add_argument("--max-workers", type=int, default=5, help="最大线程数")
    parser.add_argument("--task", choices=["edit", "repair"], required=True,
                        help="edit 或 repair；--results-path 已经是该 task 下的 leaf 目录")
    parser.add_argument("--model", required=True, help="评分模型名")
    parser.add_argument("--max-tokens", type=int, default=32 * 1024, help="最大token数")
    parser.add_argument("--max-retry", type=int, default=6, help="最大重试次数")
    parser.add_argument("--output-filename", default="judge.json", help="保存评分结果的文件名")
    args = parser.parse_args()

    BASE_DATA_PATH = args.base_data_path
    RESULTS_PATH = args.results_path
    MAX_WORKERS = args.max_workers
    TASK = args.task

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Set OPENAI_BASE_URL too if you use a non-OpenAI endpoint."
        )

    # 创建 Judge 实例
    judge = CodeJudge(
        model_name=args.model,
        api_key=api_key,
        base_url=base_url,
        max_tokens=args.max_tokens,
        max_retry=args.max_retry,
        edit_judge_prompt=EDIT_JUDGE_SYSTEM_PROMPT,
        repair_judge_prompt=REPAIR_JUDGE_SYSTEM_PROMPT,
    )

    task_result = judge_single_task_type(
        base_data_path=BASE_DATA_PATH,
        results_path=RESULTS_PATH,
        task_type=TASK,
        judge=judge,
        max_workers=MAX_WORKERS,
        output_filename=args.output_filename,
    )

    # 输出总体统计
    print(f"\n{'='*60}")
    print("OVERALL SUMMARY")
    print(f"{'='*60}")
    print(f"Total tasks: {task_result['total']}")
    print(f"Total success: {task_result['success']}")
    print(f"Total failed: {task_result['failed']}")

    if task_result["total"] > 0:
        overall_rate = task_result["success"] / task_result["total"] * 100
        print(f"Overall success rate: {overall_rate:.2f}%")

    all_failed = [r for r in task_result["results"] if r["status"] == "failed"]

    if all_failed:
        output_file = str(Path(RESULTS_PATH) / "failed_judge_tasks.txt")
        with open(output_file, "w") as f:
            for r in all_failed:
                f.write(f"[{r['task_type']}] {r['folder']}\n")
                f.write(f"  Error: {r['error']}\n")
                if "traceback" in r:
                    f.write(f"  Traceback:\n{r['traceback']}\n")
                f.write("\n")
        print(f"\n❌ Failed tasks saved to: {output_file}")

