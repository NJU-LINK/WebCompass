
import subprocess
import os
import logging
from typing import Dict, Optional

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
Docker命令执行器
用于执行复杂的Docker容器任务
"""
def run_docker(
    instance_id: str,
    agent_workspace: str,
    agent_environment: str,
    task_config_file: str,
    task_env_file: str,
    task_output_dir: str,
    docker_container_name: str,
    docker_image: str,
    network_mode: str = "host",
    timeout_duration: str = "3600s",
    cpus: str = "16",
    memory: str = "64g",
    existing_site_dir: Optional[str] = None,
    existing_site_readonly: bool = False,
) -> Dict[str, any]:
    # 验证必要的路径是否存在
    paths_to_check = [agent_workspace, agent_environment, task_config_file, task_env_file]
    for path in paths_to_check:
        if not os.path.exists(path):
            error_msg = f"路径不存在: {path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    network_config = ["--network", "host"]
    if network_mode == "bridge":
        network_config = ["--add-host=host.docker.internal:host-gateway"]

    # 透传关键环境变量（代理、鉴权、基座 URL），确保容器内工具也能用
    env_keys = [
        "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "no_proxy",
        "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN",
        "OPENAI_BASE_URL", "OPENAI_API_KEY",
    ]
    env_config = []
    for key in env_keys:
        if key in os.environ and os.environ[key] != "":
            env_config.extend(["-e", f"{key}={os.environ[key]}"])

    # 构建Docker命令
    docker_cmd = [
        "docker", "run",
        "--rm",
        "-u", "root",
        *network_config,
        "--cpus", cpus,
        "--memory", memory,
        *env_config,
        "--mount", f"type=bind,source={agent_workspace},target=/agent_workspace",
        "--mount", f"type=bind,source={agent_environment},target=/agent_environment",
        "--mount", f"type=bind,source={task_config_file},target=/agent_task/task.json",
        "--mount", f"type=bind,source={task_env_file},target=/agent_task/.task.env",
        "--mount", f"type=bind,source={task_output_dir},target=/agent_task/task_output",
        "--name", docker_container_name,
    ]

    # 如果提供了预生成站点目录，将其挂载到容器内同路径（只读可选），供 create_traj.sh 在容器内复制
    if existing_site_dir and os.path.isdir(existing_site_dir):
        mount = f"type=bind,source={existing_site_dir},target={existing_site_dir}"
        if existing_site_readonly:
            # NOTE: some Docker runtimes/filesystems (often on macOS or older kernels)
            # don't support mount_setattr used by readonly remount and will fail with 125.
            mount = mount + ",readonly"
        docker_cmd.extend(["--mount", mount])

    docker_cmd += [
        docker_image,
        "/bin/bash", "-c",
        (
            # 先修复可能的 Windows 换行符，再执行脚本
            f"sed -i 's/\\r$//' /agent_workspace/create_traj.sh && "
            f"sed -i 's/\\r$//' /agent_environment/prepare_env.sh && "
            f"timeout --signal=TERM --kill-after=30s {timeout_duration} bash -c '"
            f"/bin/bash /agent_environment/prepare_env.sh && /bin/bash /agent_workspace/create_traj.sh; "
            f"status=$?; /bin/bash /agent_environment/generate_model_patch.sh || true; exit $status'"
            f" > /agent_task/task_output/debug.log 2>&1 || echo 'Process timed out or failed'"
        ),
    ]


    print(f"执行Docker命令 [{instance_id}]: {' '.join(docker_cmd)}", flush=True)
    # python 兜底 (timeout + 10min)
    process_timeout_duration = int(timeout_duration.replace("s", "")) + 600
    try:
        # 执行Docker命令
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=process_timeout_duration  # 让Docker内部的timeout处理超时
        )

        logger.debug(f"Docker命令执行完成，返回码: {result.returncode}")

        if result.stdout:
            logger.debug(f"标准输出:\n{result.stdout}")

        if result.stderr:
            logger.debug(f"标准错误:\n{result.stderr}")

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(docker_cmd)
        }

    except subprocess.TimeoutExpired as e:
        error_msg = f"Docker命令执行超时: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

    except subprocess.CalledProcessError as e:
        error_msg = f"Docker命令执行失败: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg, "returncode": e.returncode}

    except Exception as e:
        error_msg = f"执行Docker命令时发生未知错误: {e}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
