import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Literal, Optional
from tqdm import tqdm
import argparse
from datetime import datetime

from llm.mllm.mllm_chat import MLLMChat
from llm.mllm.prompt import (
    Generation_Instruction_Prompt,
    Edit_Instruction_Prompt,
    Repair_Instruction_Prompt,
)


def get_task_folders(base_path: str) -> List[str]:
    """列出 base_path 下所有 case 目录 (base_path 应直接包含 <id>/ 子目录)。"""
    task_path = Path(base_path)
    if not task_path.exists():
        print(f"Warning: base path not found: {task_path}")
        return []

    folders = [str(f) for f in task_path.iterdir() if f.is_dir()]
    return folders


def filter_incomplete_folders(
    folders: List[str],
    model_result_path: Optional[str],
) -> List[str]:
    """当指定 model_result_path 时，只保留未完成的任务。

    model_result_path 指向 session 目录 (e.g. results/edit/<session>)。
    每个 case 的结果会写到 model_result_path/<page_type>/<id>/info.json，
    其中 <page_type> 由原始 data_folder 的父目录名派生。
    """
    if not model_result_path:
        return folders

    base = Path(model_result_path)
    incomplete = []
    for folder in folders:
        case_name = Path(folder).name
        page_type = Path(folder).parent.name
        info_path = base / page_type / case_name / "info.json"
        if not info_path.exists():
            incomplete.append(folder)
    return incomplete


def process_single_task(
    data_folder: str,
    client: MLLMChat,
    task_type: str,
    mode: str = "image",
    output_dir: str = "results/",
) -> dict:
    """处理单个任务"""
    try:
        if task_type == "generation":
            client.run_generation_task(
                data_folder=data_folder,
                mode=mode,
                output_dir=output_dir,
            )
        elif task_type in ["edit", "repair"]:
            client.run_edit_repair_task(
                data_folder=data_folder,
                mode=mode,
                task=task_type,
                output_dir=output_dir,
            )
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        return {
            "folder": data_folder,
            "task_type": task_type,
            "status": "success",
        }
    except Exception as e:
        return {
            "folder": data_folder,
            "task_type": task_type,
            "status": "failed",
            "error": str(e),
        }


def eval_single_task_type(
    base_path: str,
    task_type: str,
    client: MLLMChat,
    mode: str = "image",
    max_workers: int = 8,
    output_dir: str = "results/",
    model_result_path: Optional[str] = None,
) -> dict:
    """并行评估单个任务类型的所有任务

    Args:
        base_path: 数据集基础路径
        task_type: 任务类型 (generation/edit/repair)
        client: MLLMChat 客户端
        mode: 模式 ("image" 或 "text")
        max_workers: 最大线程数
        output_dir: 输出目录
        model_result_path: 结果路径(若指定则自动过滤已完成任务)

    Returns:
        包含结果和统计的字典
    """
    print(f"\n{'='*60}")
    print(f"Processing {task_type.upper()} tasks")
    print(f"{'='*60}")

    # 获取该任务类型的所有文件夹
    folders = get_task_folders(base_path)
    folders = filter_incomplete_folders(folders, model_result_path)
    total = len(folders)

    if total == 0:
        print(f"No {task_type} tasks found")
        return {
            "task_type": task_type,
            "total": 0,
            "success": 0,
            "failed": 0,
            "results": [],
        }

    print(f"Found {total} {task_type} tasks\n")

    results = []
    success_count = 0
    failed_count = 0

    # 使用线程池并行处理该任务类型
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_folder = {
            executor.submit(
                process_single_task, folder, client, task_type, mode, output_dir
            ): folder
            for folder in folders
        }

        # 使用tqdm显示进度
        with tqdm(total=total, desc=f"{task_type.capitalize()}") as pbar:
            for future in as_completed(future_to_folder):
                result = future.result()
                results.append(result)

                if result["status"] == "success":
                    success_count += 1
                else:
                    failed_count += 1
                    print(f"\nFailed: {result['folder']}")
                    print(f"Error: {result['error']}")

                pbar.update(1)
                pbar.set_postfix(success=success_count, failed=failed_count)

    # 输出该任务类型的统计
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
    parser = argparse.ArgumentParser(description="Batch eval runner")
    parser.add_argument("--base-path", required=True, help="数据集根目录")
    parser.add_argument("--output-dir", default="results/", help="结果输出目录")
    parser.add_argument("--mode", choices=["text", "image"], default="text")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--task", choices=["edit", "repair"], required=True,
                        help="edit 或 repair；--base-path 已经是该 task 下的 leaf 目录")
    parser.add_argument("--model", default=None, help="模型名")
    parser.add_argument("--max-tokens", type=int, default=100 * 1024)
    parser.add_argument("--max-retry", type=int, default=6)
    parser.add_argument("--timestamp", default=None, help="统一时间戳(例如 20260118_120000)")
    parser.add_argument("--model-result-path", default=None, help="指定已存在的模型结果路径，自动跳过已完成任务")
    args = parser.parse_args()

    BASE_PATH = args.base_path
    OUTPUT_DIR = args.output_dir
    MAX_WORKERS = args.max_workers
    TASK = args.task
    MODEL = args.model
    MODE = args.mode

    # 若指定 model_result_path，则自动解析 model/mode/timestamp，并写回同一目录
    if args.model_result_path:
        model_result_path = Path(args.model_result_path)
        session_name = model_result_path.name

        # 期望格式: <model>_<mode>_<YYYYMMDD>_<HHMMSS>
        parts = session_name.split("_")
        if len(parts) < 4:
            raise ValueError(
                f"Cannot parse model_result_path: {args.model_result_path}. "
                f"Expected format: <model>_<mode>_<YYYYMMDD>_<HHMMSS>"
            )

        parsed_date = parts[-2]
        parsed_time = parts[-1]
        parsed_mode = parts[-3]
        parsed_model = "_".join(parts[:-3])

        if not parsed_model or not parsed_mode or not parsed_date or not parsed_time:
            raise ValueError(
                f"Cannot parse model_result_path: {args.model_result_path}. "
                f"Expected format: <model>_<mode>_<YYYYMMDD>_<HHMMSS>"
            )

        MODEL = parsed_model
        MODE = parsed_mode
        timestamp = f"{parsed_date}_{parsed_time}"

        OUTPUT_DIR = str(model_result_path.parent)
    else:
        model_result_path = None
        timestamp = args.timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"{MODEL}_{MODE}_{timestamp}"

    # 从环境变量读取 API 凭证 (与 webcompass/ 下的 generation 评测保持一致)
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Set OPENAI_BASE_URL too if you use a non-OpenAI endpoint."
        )

    # 创建客户端 - 传入所有 prompt
    client = MLLMChat(
        model_name=MODEL,
        api_key=api_key,
        base_url=base_url,
        max_tokens=args.max_tokens,
        max_retry=args.max_retry,
        generation_prompt=Generation_Instruction_Prompt,
        edit_prompt=Edit_Instruction_Prompt,
        repair_prompt=Repair_Instruction_Prompt,
        timestamp=timestamp,
    )

    task_result = eval_single_task_type(
        base_path=BASE_PATH,
        task_type=TASK,
        client=client,
        mode=MODE,
        max_workers=MAX_WORKERS,
        output_dir=OUTPUT_DIR,
        model_result_path=str(model_result_path) if model_result_path else None,
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
        # 按 page_type 分目录，避免 sp/mp 两次运行互相覆盖失败列表
        page_type = Path(BASE_PATH).name
        failed_dir = Path(OUTPUT_DIR) / session_name / page_type
        failed_dir.mkdir(parents=True, exist_ok=True)
        output_file = failed_dir / "failed_tasks.txt"
        with open(output_file, "w") as f:
            for r in all_failed:
                f.write(f"[{r['task_type']}] {r['folder']}\n")
                f.write(f"  Error: {r['error']}\n\n")
        print(f"\nFailed tasks saved to: {output_file}")
