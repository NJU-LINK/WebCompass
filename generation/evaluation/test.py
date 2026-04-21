#!/usr/bin/env python3
# example: python -m generation.evaluation.test

import argparse
import os
import time
import json
import random
import re

import multiprocessing
import shutil
import subprocess
import glob
from pathlib import Path
from tqdm import tqdm

from .src.utils.docker import run_docker


def _guess_existing_site_dir(config: dict, instance_id: str) -> str:
    """Infer a prebuilt web project directory if user provides a root.

    Priority:
      1) config["existing_site_dir"] (full path)
      2) config["existing_site_root"] + instance_id
    Returns empty string if not configured.
    """
    if not config:
        return ""
    if config.get("existing_site_dir"):
        # allow template like "/path/{instance_id}"
        return str(config["existing_site_dir"]).format(instance_id=instance_id)
    if config.get("existing_site_root"):
        return os.path.join(str(config["existing_site_root"]), instance_id)
    return ""


def _stage_existing_site_to_output(existing_site_dir: str, task_output_dir: str) -> str:
    """Copy an existing site into task_output_dir so the original host dir won't be modified.

    Returns the staged directory path (inside task_output_dir).
    """
    if not existing_site_dir:
        return ""
    if not os.path.isdir(existing_site_dir):
        raise FileNotFoundError(f"existing_site_dir not found or not a directory: {existing_site_dir}")

    staged_dir = os.path.join(task_output_dir, "prebuilt_site")
    # Clean old staged content (if any)
    if os.path.exists(staged_dir):
        shutil.rmtree(staged_dir)
    os.makedirs(staged_dir, exist_ok=True)

    # Prefer rsync if available (fast, preserves attrs), fallback to copytree
    try:
        subprocess.run(
            [
                "rsync",
                "-a",
                "--delete",
                f"{existing_site_dir.rstrip('/')}/",
                f"{staged_dir.rstrip('/')}/",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        # shutil.copytree wants destination not to exist
        shutil.rmtree(staged_dir)
        shutil.copytree(existing_site_dir, staged_dir, dirs_exist_ok=False)

    return staged_dir


def _sync_dir(src_dir: str, dst_dir: str) -> None:
    """Best-effort sync from src_dir to dst_dir.

    Prefer rsync for speed and to remove deleted files; fallback to copytree.
    """
    if not src_dir or not dst_dir:
        return
    if not os.path.isdir(src_dir):
        raise FileNotFoundError(f"sync src_dir not found or not a directory: {src_dir}")

    os.makedirs(dst_dir, exist_ok=True)
    try:
        subprocess.run(
            [
                "rsync",
                "-a",
                "--delete",
                f"{src_dir.rstrip('/')}/",
                f"{dst_dir.rstrip('/')}/",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        # Fallback: crude but works
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=False)


def _get_resume_site_dir(output_dir: str, instance_id: str) -> str:
    """Persistent resume directory under output_dir/resume_site/<instance_id>."""
    return os.path.join(output_dir, "resume_site", instance_id)


def _check_any_pending_in_dir(site_dir: str) -> bool:
    """Return True if checklist.json contains score == null.

    We intentionally avoid strict JSON parsing here.

    Rationale:
      - Some checklists may be partially-written / contain non-strict JSON due to
        unescaped quotes, control chars, etc.
      - For resume logic, we only need a robust *signal* of whether there is any
        pending work left.

        Policy:
            - Missing/empty/unreadable files => treat as NOT pending (no need to continue)
            - Otherwise, scan the raw text for a "score": null pattern.
    """
    if not site_dir:
        return False

    import re

    pending_pat = re.compile(r'"score"\s*:\s*null', re.IGNORECASE)

    fp = os.path.join(site_dir, "checklist.json")
    if not os.path.exists(fp) or os.path.getsize(fp) == 0:
        # 缺失/空文件：按新口径认为无需续跑
        return False
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if pending_pat.search(content):
            return True
    except Exception:
        # 读失败：按新口径认为无需续跑
        return False

    return False


def _check_pending(site_dir: str) -> bool:
    """Backward-compatible wrapper for single-file checklist pending status."""
    return _check_any_pending_in_dir(site_dir)


AGENT_ENV_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "environment")

TASK_DESCRIPTION = """
<task>
{problem_statement}
</task>

Based on the design requirements in <task>, generate a complete web project repository.
"""

VERIFY_DESCRIPTION_IMAGE = """
<pr_description>
You are a strict website tester. Your job is to evaluate the webpage's execution, aesthetics, and interactivity based on the checklist (verification and scoring only, no fixes).
Here is the user's requirement document:
<docs>
{instruction}
</docs>

Your goal: Based on real user browsing paths (give low scores if users cannot properly use webpage functions), use mcp_tools: mcp__chrome-devtools to verify whether each checklist requirement is met. Update all items with score=null in checklist.json with specific scores, provide reproducible evidence (reason), and save screenshots to image/.

========================
Mandatory Rules (Must Follow)
========================
1) DO NOT modify/fix the original website project code.
2) You are ONLY allowed to create/modify:
    - checklist.json
    - Screenshot files in the image/ directory
3) Complete all tasks in one session. Before completing all tasks, you must call tools for verification in each round, following Claude Code format requirements. Only explain blockers in the reason field if verification is truly impossible.

========================
Scope (Single Checklist File)
========================
1) You only process one checklist file: checklist.json
2) As long as there are items with score=null in this file, you must continue verifying and filling in scores until no score=null remains.
3) For aesthetic evaluation tasks requiring visual input, you must use UI screenshots for scoring.

========================
Mandatory Workflow (Follow in Order, No Skipping)
========================

Step 0: Prepare Output Directory
1) Ensure the image/ folder exists in the project directory (create if not exists).
2) Take screenshots for each key state verification and save to image/ (full-page screenshots recommended).
3) Review reference images under screenshots/

Step 1: Code Review First (Read-Only)
1) Quickly read code related to page entry, routing, interactions, requests, and error handling (read-only).
2) From the code review, identify verification points: entry URLs/page paths, key buttons/forms, potential error points, data sources and loading logic, etc.
3) Note: Code review is only for guiding test paths and predicting risks. Final scores must be based on actual webpage behavior.

Step 2: Read checklist.json (Get Test Tasks)
1) Read the file and locate all items with score=null.
2) For each item, extract task / operation_sequence / expected_result (if present) to clarify what to do and observe.

Step 3: Open and Test the Webpage (Real User Journey)
1) Start the webpage using python -m http.server 8000 (or another port).
2) Use mcp__chrome-devtools to open the webpage via URL for interactive verification (may include clicking, typing, navigation, scrolling, refreshing, going back, etc.).
3) For each item verification: execute user operations as required, observe if expectations are met. For items requiring reference image comparison, first take a screenshot of the corresponding webpage interface, then compare with the reference image.
4) For aesthetic test tasks, navigate to the corresponding webpage and name screenshots according to “webpage_screenshot_path”.

Step 4: Write Back to Checklist Immediately (Test and Write)
1) After completing each verification, immediately write back to checklist.json:
   - score: Change from null to a specific score (strictly following item criteria).
   - reason: Must be a single-line string without double quotes, containing reproducible evidence (page/operation/phenomenon/screenshot filename).
2) For items where score is already non-null: If new evidence is sufficient to overturn the previous conclusion, you may update score and reason.

========================
Critical Rule: Entry Failure => Cascade Failure
========================
If the website entry is unavailable (won't open/blank screen/crash/infinite loading/key navigation inoperable/main content inaccessible):
1) You must first take a screenshot as evidence and record the reason.
2) All items in this category that depend on the entry should be handled as unable to verify:
   - If scoring criteria allow, give a failure/minimum score and explain why.
   - If reliable judgment is truly impossible, you may temporarily keep score=null, but reason must clearly state what you tried, where you got stuck, and suggestions for continuing verification next time (e.g., needs backend data/needs login account/needs longer wait, etc.).

========================
End Condition
========================
You may only end this task when there are NO items with score=null in checklist.json.

</pr_description>

Please help me solve the task specified in <pr_description>. and please use the mcp_tools: mcp__chrome-devtools to verify your results.
"""

VERIFY_DESCRIPTION = """
<pr_description>
You are a strict QA website tester. Your task is to rigorously evaluate webpage execution, aesthetics, and interactive functionality based on a checklist (verification and scoring only, no fixes).
Below is the user's requirement document for the webpage:
<docs>
{instruction}
</docs>

Your goal: Based on a real user's browsing journey (if users cannot properly use webpage features from their perspective, give low scores), use mcp_tools: mcp__chrome-devtools to verify whether each checklist requirement is met. Update all items in checklist.json where score is null with explicit scores, provide reproducible evidence (reason), and save screenshots to image/.

========================
Mandatory Rules (Must Follow)
========================
1) DO NOT modify/fix the original website project code: including but not limited to HTML/CSS/JS/TS/backend code, build configs, dependencies, etc.
2) You are ONLY allowed to create/modify:
    - checklist.json
   - Screenshot files in image/ directory
3) Complete all tasks in one run. Before completing all tasks, each iteration must call tools for verification, ensuring format meets Claude Code requirements; only note blockers in reason if verification is truly impossible.

========================
Scope (Single Checklist File)
========================
1) You only process one checklist file: checklist.json
2) As long as the file still has items with score as null, you must continue verifying and filling in, until checklist.json has no score=null items.
3) For aesthetic tasks requiring visual input, you must combine UI screenshots for scoring.

========================
Mandatory Workflow (Follow in Order, No Skipping)
========================

Step 0: Prepare Output Directory
1) Ensure image/ folder exists in project directory (create if not exists).
2) Save screenshots to image/ for each key state verification (full page screenshots recommended).

Step 1: Code Review First (Read-Only)
1) Quickly read repository code related to page entry, routing, interactions, requests, error handling (read-only).
2) Extract verifiable points from code review: entry URL/page paths, key buttons/forms, potential error points, data sources and loading logic, etc.
3) Note: Code review only guides test paths and anticipates risks; final scores must be based on actual webpage behavior.

Step 2: Read checklist.json (Get Test Tasks Item by Item)
1) Read the file and locate all items with score as null.
2) For each item, extract task / operation_sequence / expected_result (if present), clarify what to operate and observe.

Step 3: Open and Actually Test Webpage (Real User Journey)
1) Use mcp__chrome-devtools for interactive verification (click, input, navigate, scroll, refresh, back, etc.). Do not use file addresses as URLs to open webpages.
2) For each item verification: execute user operations as required, observe if expectations are met, take screenshots as evidence (including key UI or error messages). For aesthetic tasks requiring visual input, combine UI screenshots for scoring.

Step 4: Write Back to Checklist Immediately (Test and Write)
1) After completing each verification, immediately write back to checklist.json:
   - score: Change from null to explicit score (strictly follow item criteria).
   - reason: Must be a single-line string without double quotes, containing reproducible evidence (page/operation/phenomenon/screenshot filename).
2) For items where score is already non-null: if new evidence is sufficient to overturn the original conclusion, you may update score and reason.

========================
Critical Rule: Entry Failure => Cascade Failure
========================
If the website entry is unavailable (cannot open/blank page/crash/infinite loading/key navigation inoperable/main content inaccessible):
1) Must take screenshot as evidence and record in reason first.
2) All items in this category depending on entry should be processed under the principle of unable to complete verification:
   - If scoring criteria allow, give failure/minimum score and explain the reason.
   - If truly unable to reliably determine, you may temporarily keep score=null, but reason must clearly state what you tried, where you got stuck, and suggestions for next verification attempt (e.g., needs backend data/needs login account/needs longer wait, etc.).

========================
End Condition
========================
You may only end this task when and only when there are no items with score as null in checklist.json.

</pr_description>

Please help me solve the task specified in <pr_description>. and please use the mcp_tools: mcp__chrome-devtools to verify your results.
"""

def run_sginle_task(task_metadata):
    task = task_metadata["task"]
    output_dir = task_metadata["output_dir"]
    agent_dir = task_metadata["agent_dir"]
    existing_site_dir = task_metadata.get("existing_site_dir")
    retry_count = int(task_metadata.get("retry_count", 1))

    # Single checklist mode: always 1 verification phase.
    
    task_config_dir = os.path.join(output_dir, task["instance_id"])
    os.makedirs(task_config_dir, exist_ok=True)

    task_config_file = os.path.join(task_config_dir, "task.json")
    with open(task_config_file, "w") as f:
        json.dump(task, f, indent=4, ensure_ascii=False)

    task_env_file = task_config_file.replace("task.json", ".task.env")
    with open(task_env_file, "w") as f:
        # 配置 dot env 文件
        f.write(f'OPENAI_BASE_URL=""\n')

    # We'll run docker in a retry loop when any checklist item is still pending.
    # Each attempt uses its own task_output_dir to keep logs/artifacts separated.

    # ------------------------------------------------------------------
    # Persistent resume site (方案A):
    # - Use output_dir/resume_site/<instance_id> as a writable, persistent site.
    # - First run: initialize it from existing_site_dir (if provided).
    # - Next runs: reuse it directly (continue from previous state).
    # ------------------------------------------------------------------
    resume_site_dir = _get_resume_site_dir(output_dir, task["instance_id"])
    resume_inited = os.path.isdir(resume_site_dir) and any(os.scandir(resume_site_dir))
    if (not resume_inited) and existing_site_dir and os.path.isdir(existing_site_dir):
        # Initialize resume dir from the provided existing site
        try:
            _sync_dir(existing_site_dir, resume_site_dir)
            resume_inited = True
        except Exception as e:
            print(f"[{task['instance_id']}] 初始化 resume_site_dir 失败: {e}", flush=True)

    # Always prefer resume_site_dir for container to work on (if it exists)
    if os.path.isdir(resume_site_dir) and any(os.scandir(resume_site_dir)):
        existing_site_dir = resume_site_dir

    # ------------------------------------------------------------------
    # Pre-create checklist.json with default score=null.
    # IMPORTANT: put it into resume_site_dir (persistent), so score values
    # can be resumed next run.
    # ------------------------------------------------------------------
    def _init_checklist_items(items):
        def _normalize_text(v):
            """Normalize text fields to make checklist JSON stable across runs.

            We convert actual newlines into the literal `\\n` sequence so that
            downstream agents won't keep retrying due to formatting differences.
            """
            if isinstance(v, str):
                return v.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
            return v

        initialized = []
        for idx, it in enumerate(items, start=1):
            obj = dict(it) if isinstance(it, dict) else {"task": str(it)}
            obj.setdefault("id", idx)

            # Normalize multi-line or noisy text fields.
            for k in ("task", "operation_sequence", "expected_result", "reason"):
                if k in obj:
                    obj[k] = _normalize_text(obj.get(k))

            # New scoring-based status:
            # - score: null => pending/unverified
            # - score: non-null => verified/scored
            obj["score"] = None
            obj.setdefault("reason", "")
            initialized.append(obj)
        return initialized

    # Parse the original checklist from the task's problem_statement.
    # problem_statement is a <task> wrapper string; we can still extract JSON
    # by locating the first '[' and last ']'. If parsing fails, we skip.
    try:
        ps = task.get("problem_statement", "")
        lbr = ps.find("[")
        rbr = ps.rfind("]")
        raw_json = ps[lbr : rbr + 1] if lbr != -1 and rbr != -1 and rbr > lbr else ""
        checklist_all = json.loads(raw_json) if raw_json else []
    except Exception:
        checklist_all = []

    checklist_payload = _init_checklist_items(checklist_all)

    # Create only if missing, so we don't reset pass/fail from previous runs.
    if existing_site_dir:
        fpath = os.path.join(existing_site_dir, "checklist.json")
        if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
            try:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(checklist_payload, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[{task['instance_id']}] 写入 checklist.json 失败: {e}", flush=True)

    last_result = {"success": False}
    # attempt_idx starts from 1.
    for attempt_idx in range(1, max(1, retry_count) + 1):
        # Stop early if no pending remains (pass/fail finished)
        if attempt_idx > 1 and not _check_any_pending_in_dir(resume_site_dir):
            break
        # Single checklist mode: no per-category skipping.

        # 创建一个随机的 output 目录 (+ 时间戳 + random value)
        task_output_dir = os.path.join(
            task_config_dir,
            "output_" + str(time.time()) + "_" + str(random.randint(1, 10000)) + f"_attempt{attempt_idx}",
        )
        os.makedirs(task_output_dir, exist_ok=True)

        # If we have a prebuilt/resume site, stage a copy into this run's output dir to avoid polluting it.
        staged_existing_site_dir = ""
        if existing_site_dir:
            try:
                staged_existing_site_dir = _stage_existing_site_to_output(existing_site_dir, task_output_dir)
            except Exception as e:
                print(f"[{task['instance_id']}] 预拷贝 existing_site_dir 失败: {e}", flush=True)
                staged_existing_site_dir = ""

        if staged_existing_site_dir:
            # Ensure task.json carries the staged path for container-side script
            task["existing_site_dir"] = staged_existing_site_dir
            with open(task_config_file, "w") as f:
                json.dump(task, f, indent=4, ensure_ascii=False)

        print(f"[{task['instance_id']}] 开始第 {attempt_idx}/{retry_count} 次续跑（若仍有未评分条目：score=null）", flush=True)
        last_result = run_docker(
            instance_id=task["instance_id"],
            agent_workspace=agent_dir,
            agent_environment=AGENT_ENV_DIR,
            task_config_file=task_config_file,
            task_env_file=task_env_file,
            task_output_dir=task_output_dir,
            docker_container_name=f"{agent_dir.split('/')[-1]}_{random.randint(1,10000)}",
            docker_image=task["docker_image"],
            network_mode=task.get("network_mode", "host"),
            existing_site_dir=staged_existing_site_dir or None,
            existing_site_readonly=False,
        )

        # After run: sync generated site back to persistent resume_site_dir
        try:
            working_dir = task.get("working_dir", "/testbed").lstrip("/")
            generated_site_dir = os.path.join(task_output_dir, "generated_web_pages", working_dir)
            if os.path.isdir(generated_site_dir):
                _sync_dir(generated_site_dir, resume_site_dir)
                existing_site_dir = resume_site_dir
        except Exception as e:
            print(f"[{task['instance_id']}] 回写到 resume_site_dir 失败: {e}", flush=True)

        # If docker run itself failed, still allow retries; but if this is last attempt, exit.
        if attempt_idx < retry_count and _check_any_pending_in_dir(resume_site_dir):
            continue

    # Final status
    if not _check_any_pending_in_dir(resume_site_dir):
        print(f"{task['instance_id']} checklist 已全部完成（无 score=null）", flush=True)
        return "成功"

    # Still pending or errors
    if last_result.get("success"):
        print(f"{task['instance_id']} 容器执行成功但仍有 score=null（达到最大续跑次数）", flush=True)
    else:
        print(f"{task_config_dir} 任务执行失败或未完成（达到最大续跑次数）", flush=True)
    return "失败"

def _run_with_config(config: dict) -> None:
    tasks_file = config["tasks_file"]

    agent_dir = config["agent_dir"]

    num_tasks = config["num_tasks"]
    num_processes = config["num_processes"]
    retry_count = config["retry_count"]

    output_dir = config["output_dir"]

    anthropic_auth_token = config["anthropic_auth_token"]
    anthropic_base_url = config["anthropic_base_url"]

    # Optional: model routing hint (used by create_traj.sh -> claude --model)
    model = config.get("model", "")

    # 从tasks_file的路径中提取文件名作为任务名称
    task_info_list = []
    with open(tasks_file, 'r') as f:
        lines = f.readlines()
        for line in tqdm(lines):
            try:
                if "Error during processing: Command" in line:
                    continue

                line = line.strip()
                task_info = json.loads(line)
                task_info_list.append(task_info)
            except Exception as e:
                print(line)
    
    if "start_index" in config and "end_index" in config:
        start_index = config["start_index"]
        end_index = config["end_index"]
        if start_index < len(task_info_list) and start_index < end_index:
            task_info_list = task_info_list[start_index:end_index]

    if num_tasks > 0 and len(task_info_list) > num_tasks:
        task_info_list = task_info_list[:num_tasks]

    task_metadata_list = []
    for i, task_info in tqdm(enumerate(task_info_list), total=len(task_info_list)):
        problem_statement = task_info["problem_statement"]
        # Extra natural-language instruction for QA (optional)
        # Some datasets include an `instruction` field; if missing, fallback to empty.
        instruction = task_info.get("instruction", "")
        # `problem_statement` may already be a parsed object (list/dict),
        # or it may be a JSON string. Be tolerant here.
        if isinstance(problem_statement, (list, dict)):
            checklist = problem_statement
        elif isinstance(problem_statement, (str, bytes, bytearray)):
            try:
                checklist = json.loads(problem_statement)
            except Exception:
                # Keep running even if this one record is malformed.
                checklist = []
        else:
            checklist = []

        checklist = checklist or []
        # Execution | Interaction | Aesthetics
        # Be tolerant: some datasets may contain non-dict items or missing keys.
        # Single checklist mode: keep the raw checklist as-is.
        working_dir = task_info.get("working_dir", "/testbed")
        instance_id = task_info["instance_id"]

        # Ensure <task> section is JSON-serializable and stable.
        # If it's a list/dict, dump as JSON so downstream parsing works.
        ps_for_prompt = problem_statement
        if isinstance(problem_statement, (list, dict)):
            ps_for_prompt = json.dumps(problem_statement, ensure_ascii=False)

        problem_statement_fmt = TASK_DESCRIPTION.format(
            problem_statement=ps_for_prompt
        )
        problem_statement_fmt = problem_statement_fmt.strip()

        verify_command_fmt = VERIFY_DESCRIPTION.format(
            instruction=str(instruction),
            problem_statement=json.dumps(checklist, ensure_ascii=False),
            category="all",
        ).strip()

        task_config_dir = os.path.join(output_dir, instance_id)
        # Skip rule (resume-based):
        # - If resume_site/<instance_id> exists and has NO pending items (all pass/fail), we skip.
        # - Otherwise (still pending / missing / invalid), we include it so re-running this script
        #   will automatically resume unfinished instances.
        resume_site_dir = _get_resume_site_dir(output_dir, instance_id)
        if os.path.isdir(resume_site_dir) and any(os.scandir(resume_site_dir)):
            if not _check_any_pending_in_dir(resume_site_dir):
                print(f"{instance_id} resume_site 已完成（无 score=null），跳过")
                continue
            else:
                print(f"{instance_id} resume_site 仍有 score=null，继续续跑")
        
        task = {
            "repo_name": task_info["repo"],
            "instance_id": instance_id,
            "docker_image": "web_bench/base",
            "base_commit": "main",
            "model": model,
            "problem_statement": problem_statement_fmt,
            # Single-pass verification (full checklist)
            "verify_command": verify_command_fmt,
            "working_dir": working_dir,
            "anthropic_auth_token": anthropic_auth_token,
            "anthropic_base_url": anthropic_base_url,
            "target_image_owner": "web_bench",
            "target_image_name": "base",
            "target_image_version": "latest",
            "network_mode": "bridge"
        }

        # Optional: reuse an existing prebuilt web project
        existing_site_dir = _guess_existing_site_dir(config, instance_id)
        if existing_site_dir:
            task["existing_site_dir"] = existing_site_dir

        task_metadata = {
            "task": task,
            "output_dir": output_dir,
            "agent_dir": agent_dir,
            "existing_site_dir": existing_site_dir,
            "retry_count": retry_count,
        }

        task_metadata_list.append(task_metadata)
    
    print(f"Start {num_processes} processes for {len(task_metadata_list)} tasks")

    # 多进程处理任务
    # 使用多进程池执行任务
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = list(tqdm(
            pool.imap(run_sginle_task, task_metadata_list),
            total=len(task_metadata_list),
            desc="处理任务进度"
        ))
    
    # 统计结果
    success_count = sum(1 for result in results if "成功" in result)
    failure_count = len(results) - success_count
    
    print(f"\n执行完成！")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="WebCompass Evaluation Runner")
    parser.add_argument("--config", type=str, required=True, help="Path to config JSON file")
    parser.add_argument("--models", type=str, default=None, help="Comma-separated list of model names (overrides config)")
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = json.load(f)

    # 获取模型列表：优先使用命令行参数，否则使用配置文件中的 model 字段
    if args.models:
        model_list = [m.strip() for m in args.models.split(",") if m.strip()]
    elif config.get("model"):
        model_list = [config["model"]]
    else:
        print("错误：请通过 --models 参数或配置文件中的 model 字段指定模型")
        return

    output_dir_base = os.path.dirname(config["output_dir"].rstrip("/"))
    existing_site_root_base = os.path.dirname(config["existing_site_root"].rstrip("/"))

    for model_name in model_list:
        model_config = dict(config)
        model_config["output_dir"] = os.path.join(output_dir_base, model_name)
        model_config["existing_site_root"] = os.path.join(existing_site_root_base, model_name)
        model_config["model"] = model_name
        print(
            f"\n=== 处理模型: {model_name} ===\n"
            f"output_dir: {model_config['output_dir']}\n"
            f"existing_site_root: {model_config['existing_site_root']}\n"
        )
        _run_with_config(model_config)


if __name__ == '__main__':
    main()

