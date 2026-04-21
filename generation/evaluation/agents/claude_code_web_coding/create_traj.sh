#!/usr/bin/env bash

# 尽量不要依赖 ~/.bashrc（容器里常常不存在或不含 python PATH）
if [ -f ~/.bashrc ]; then
    # shellcheck disable=SC1090
    source ~/.bashrc
fi

# 选择一个可用的 python 解释器
WORKSPACE_PYTHON=""
for candidate in python3 python /usr/bin/python3 /usr/local/bin/python3 /opt/conda/bin/python /opt/conda/bin/python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        WORKSPACE_PYTHON=$(command -v "$candidate")
        break
    fi
    if [ -x "$candidate" ]; then
        WORKSPACE_PYTHON="$candidate"
        break
    fi
done

echo "WORKSPACE_PYTHON: ${WORKSPACE_PYTHON}"
if [ -z "$WORKSPACE_PYTHON" ]; then
    echo "[create_traj] ERROR: python not found in PATH; please ensure python3 is installed in the container image" >&2
    exit 10
fi


# 启动google-chrome
nohup google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile \
  --no-sandbox \
  --headless=new \
  --use-gl=angle \
  --use-angle=swiftshader \
  --enable-unsafe-swiftshader \
  --enable-webgl \
  --ignore-gpu-blocklist &



# 创建一个临时目录用于存放 python 软链接
TEMP_BIN_DIR="/tmp/python_bin"
if [ -e "$TEMP_BIN_DIR" ]; then
    echo "Directory $TEMP_BIN_DIR already exists. Deleting it."
    rm -rf "$TEMP_BIN_DIR"
fi

# 让 python 直接指向 WORKSPACE_PYTHON, 不需要依赖 shell 初始化脚本
mkdir -p "$TEMP_BIN_DIR"
ln -sf "$WORKSPACE_PYTHON" "$TEMP_BIN_DIR/python"
export PATH="$TEMP_BIN_DIR:$PATH"
echo "Created python symlink at $TEMP_BIN_DIR/python -> $WORKSPACE_PYTHON"
ls -al "$TEMP_BIN_DIR/python"
# 安装 chrome-devtools-mcp
claude mcp add chrome-devtools npx chrome-devtools-mcp@0.12.1

# NOTE: 不使用 set -e，因为 claude/mcp 在不同环境可能返回非 0，避免整条流水线被提前中断。

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)
TASK_OUTPUT_DIR="/agent_task/task_output"
TASK_CONFIG_FILE="/agent_task/task.json"

# claude 配置文件（随 agent 分发）
CLAUDE_SETTINGS_SRC="${CURRENT_DIR}/settings/settings.json"

WORKING_DIR=$(jq -r '.working_dir' "$TASK_CONFIG_FILE")
BASE_COMMIT=$(jq -r '.base_commit' "$TASK_CONFIG_FILE")

ANTHROPIC_BASE_URL=$(jq -r '.anthropic_base_url' "$TASK_CONFIG_FILE")
ANTHROPIC_AUTH_TOKEN=$(jq -r '.anthropic_auth_token' "$TASK_CONFIG_FILE")

# 一些上游 provider 需要 ANTHROPIC_API_KEY（ccr 转发时会用到）。
# 兼容：我们这套任务配置经常只提供 anthropic_auth_token（形如 sk-*），这里兜底将其作为 ANTHROPIC_API_KEY。
TASK_ANTHROPIC_API_KEY_SOURCE=""
TASK_ANTHROPIC_API_KEY=$(jq -r '.anthropic_api_key // .anthropicApiKey // .api_key // .apiKey // empty' "$TASK_CONFIG_FILE" 2>/dev/null || true)
if [ -n "$TASK_ANTHROPIC_API_KEY" ] && [ "$TASK_ANTHROPIC_API_KEY" != "null" ]; then
    TASK_ANTHROPIC_API_KEY_SOURCE="task.json:anthropic_api_key"
else
    TASK_ANTHROPIC_API_KEY=$(jq -r '.anthropic_auth_token // .anthropicAuthToken // empty' "$TASK_CONFIG_FILE" 2>/dev/null || true)
    if [ -n "$TASK_ANTHROPIC_API_KEY" ] && [ "$TASK_ANTHROPIC_API_KEY" != "null" ]; then
        TASK_ANTHROPIC_API_KEY_SOURCE="task.json:anthropic_auth_token"
    fi
fi

if [ -n "$TASK_ANTHROPIC_API_KEY" ] && [ "$TASK_ANTHROPIC_API_KEY" != "null" ]; then
    export ANTHROPIC_API_KEY="$TASK_ANTHROPIC_API_KEY"
fi

# 读取 model（用于 claude --model）
# 优先级：
#   1) task.json 里的 .model（推荐：由上游调度脚本写入，容器内必然可读）
#   2) lab_api.json 里的 .model（仅当容器内存在该文件时）
MODEL_ARG=""

MODEL_FROM_TASK=$(jq -r '.model // empty' "$TASK_CONFIG_FILE" 2>/dev/null || true)
if [ -n "$MODEL_FROM_TASK" ] && [ "$MODEL_FROM_TASK" != "null" ]; then
    MODEL_ARG="$MODEL_FROM_TASK"
else
    # fallback to lab_api.json
    LAB_API_JSON_DEFAULT="${CURRENT_DIR}/../../configs/lab_api.json"
    LAB_API_JSON="${LAB_API_JSON:-$LAB_API_JSON_DEFAULT}"
    if [ -f "$LAB_API_JSON" ]; then
        MODEL_FROM_LAB=$(jq -r '.model // empty' "$LAB_API_JSON" 2>/dev/null || true)
        if [ -n "$MODEL_FROM_LAB" ] && [ "$MODEL_FROM_LAB" != "null" ]; then
            MODEL_ARG="$MODEL_FROM_LAB"
        fi
    fi
fi

if [ -n "$MODEL_ARG" ]; then
    echo "[create_traj] Using model: $MODEL_ARG"
else
    echo "[create_traj] WARN: model is empty (task.json/lab_api.json); will not pass --model"
fi

# 安装 agent
bash ${CURRENT_DIR}/install_packages.sh

# ------------------------------------------------------------------
# QA runner 约束：通常只允许写 checklist 和 image/ 目录下的截图。
# 为了避免模型在任务开始阶段反复尝试 `mkdir -p image/`（触发 Bash 前缀检测/审批回环），
# 这里在进入任务前就预创建好 image/ 目录（在 WORKING_DIR 下）。
# ------------------------------------------------------------------
if [ -n "$WORKING_DIR" ] && [ "$WORKING_DIR" != "null" ] && [ -d "$WORKING_DIR" ]; then
    ( \
        cd "$WORKING_DIR" && \
        mkdir -p image && \
        echo "[create_traj] Pre-created $WORKING_DIR/image (avoids repeated mkdir tool calls in QA runs)." \
    ) >>"${TASK_OUTPUT_DIR}/create_traj.log" 2>&1 || true
else
    echo "[create_traj] WARN: WORKING_DIR is invalid or not found; skip pre-creating image/: $WORKING_DIR" >>"${TASK_OUTPUT_DIR}/create_traj.log" 2>&1 || true
fi

# ------------------------------------------------------------------
# Prepare claude settings
#   settings.json -> ~/.claude/settings.json
# Note: 不再使用 claude-code-router(ccr)，避免额外依赖/端口/代理复杂度。
#       claude 将直接使用 task.json 注入的 ANTHROPIC_BASE_URL/ANTHROPIC_AUTH_TOKEN。
# ------------------------------------------------------------------
mkdir -p ~/.claude

if [ -f "$CLAUDE_SETTINGS_SRC" ]; then
    cp -f "$CLAUDE_SETTINGS_SRC" ~/.claude/settings.json
    echo "[create_traj] Installed claude settings: ~/.claude/settings.json"
else
    echo "[create_traj] WARN: claude settings not found: $CLAUDE_SETTINGS_SRC" >&2
fi

# 输出重定向
touch "${TASK_OUTPUT_DIR}/create_traj.log"

PARALLEL_TOOL_CALL_MD="${CURRENT_DIR}/settings/PARALLEL_TOOL_CALL.md"

TEMP_PROBLEM_FILE="/agent_task/task_output/problem_statement"
PROBLEM_STATEMENT=$(jq -r '.problem_statement' "$TASK_CONFIG_FILE")
echo "$PROBLEM_STATEMENT" > "$TEMP_PROBLEM_FILE"

TEMP_VERIFY_FILE="/agent_task/task_output/verify_command"
VERIFY_COMMAND=$(jq -r '.verify_command // empty' "$TASK_CONFIG_FILE")
echo "$VERIFY_COMMAND" > "$TEMP_VERIFY_FILE"

####################################################################
# Optional: use an existing pre-generated web project (read-only mount)
#
# If host provides a prebuilt project and run_docker mounts it into the
# container at the same path (usually read-only), set:
#   - EXISTING_SITE_DIR=/abs/path/on/host
# This script will copy it into WORKING_DIR before running verification.
####################################################################
# Allow both env var override and task.json field (if future-proofed)
EXISTING_SITE_DIR="${EXISTING_SITE_DIR:-}"
if [ -z "$EXISTING_SITE_DIR" ]; then
    # jq returns "null" for missing keys; treat as empty
    EXISTING_SITE_DIR=$(jq -r '.existing_site_dir // empty' "$TASK_CONFIG_FILE" 2>/dev/null || true)
fi

mkdir -p "${WORKING_DIR}"

if [ -n "$EXISTING_SITE_DIR" ]; then
    echo "[create_traj] EXISTING_SITE_DIR is set: ${EXISTING_SITE_DIR}"
    if [ ! -d "$EXISTING_SITE_DIR" ]; then
        echo "[create_traj] ERROR: EXISTING_SITE_DIR does not exist or not a directory: ${EXISTING_SITE_DIR}" >&2
        exit 2
    fi

    # Copy into WORKING_DIR so subsequent steps can write freely
    echo "[create_traj] Copying prebuilt site into WORKING_DIR: ${WORKING_DIR}"
    # Clear working dir to avoid mixing runs
    rm -rf "${WORKING_DIR:?}"/*
    cp -a "${EXISTING_SITE_DIR}"/. "${WORKING_DIR}"/

    # By default, skip Step 1 when using an existing site
    SKIP_STEP1="${SKIP_STEP1:-1}"
else
    SKIP_STEP1="${SKIP_STEP1:-0}"
fi

cd ${WORKING_DIR}

# unset -v http_proxy https_proxy no_proxy

export PATH="/usr/local/bin:${PATH}"
export CLAUDE_CODE_SKIP_BEDROCK_AUTH=1
export DISABLE_AUTOUPDATER=1
export ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL}
export ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN}
export IS_SANDBOX=1
export API_TIMEOUT_MS=600000
export BASH_DEFAULT_TIMEOUT_MS=600000
export BASH_MAX_TIMEOUT_MS=1200000
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1

# Optional: Set proxy if needed (uncomment and configure)
# export http_proxy=http://your-proxy:port
# export https_proxy=http://your-proxy:port


export CLAUDE_CODE_LOG_DIR=${TASK_OUTPUT_DIR}

# Step 1: Generate Web Page Code
if [ "$SKIP_STEP1" = "1" ]; then
    echo "Step 1: Skipped (using prebuilt web project)"
    # Keep log placeholders consistent
    : > "${TASK_OUTPUT_DIR}/create_traj_step1.log"
    if [ -f "${TASK_OUTPUT_DIR}/messages.log" ]; then
        cp "${TASK_OUTPUT_DIR}/messages.log" "${TASK_OUTPUT_DIR}/messages.log.p1"
    else
        : > "${TASK_OUTPUT_DIR}/messages.log.p1"
    fi
else
    echo "Step 1: Generating Web Page Code..."
    CLAUDE_CMD=(
        claude --verbose
        -p
        --model opus
        --dangerously-skip-permissions
        --permission-mode bypassPermissions
        --output-format stream-json
        --max-turns 150
        --append-system-prompt "$(cat "$PARALLEL_TOOL_CALL_MD")"
        "$(cat "$TEMP_PROBLEM_FILE")"
    )
    "${CLAUDE_CMD[@]}" >> "${TASK_OUTPUT_DIR}/create_traj_step1.log" 2>&1

    cp "${TASK_OUTPUT_DIR}/messages.log" "${TASK_OUTPUT_DIR}/messages.log.p1"
fi

# Step 2: Verify and Checklist (single pass)
echo "Step 2: Verifying and Creating Checklist..."
if [ -s "$TEMP_VERIFY_FILE" ]; then
    CLAUDE_CMD=(
        claude --verbose
        -p
        --model opus
        --dangerously-skip-permissions
        --permission-mode bypassPermissions
        --output-format stream-json
        --max-turns 150
        --append-system-prompt "$(cat "$PARALLEL_TOOL_CALL_MD")"
        "$(cat "$TEMP_VERIFY_FILE")"
    )
    "${CLAUDE_CMD[@]}" >> "${TASK_OUTPUT_DIR}/create_traj_step2.log" 2>&1

    if [ -f "${TASK_OUTPUT_DIR}/messages.log" ]; then
        cp "${TASK_OUTPUT_DIR}/messages.log" "${TASK_OUTPUT_DIR}/messages.log.p2"
    else
        : > "${TASK_OUTPUT_DIR}/messages.log.p2"
    fi
else
    echo "[create_traj] WARN: verify_command is empty, skipping" >> "${TASK_OUTPUT_DIR}/create_traj_step2.log"
    : > "${TASK_OUTPUT_DIR}/messages.log.p2"
fi

# Merge p1 and p2 into messages.log
rm -f "${TASK_OUTPUT_DIR}/messages.log"
touch "${TASK_OUTPUT_DIR}/messages.log"
if [ -f "${TASK_OUTPUT_DIR}/messages.log.p1" ]; then
    cat "${TASK_OUTPUT_DIR}/messages.log.p1" >> "${TASK_OUTPUT_DIR}/messages.log"
fi
if [ -f "${TASK_OUTPUT_DIR}/messages.log.p2" ]; then
    cat "${TASK_OUTPUT_DIR}/messages.log.p2" >> "${TASK_OUTPUT_DIR}/messages.log"
fi

cp -r ~/.claude "${TASK_OUTPUT_DIR}"

mkdir -p "${TASK_OUTPUT_DIR}/generated_web_pages"
cp -r "${WORKING_DIR}" "${TASK_OUTPUT_DIR}/generated_web_pages"
