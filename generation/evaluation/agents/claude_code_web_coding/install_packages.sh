#!/bin/bash
set -e

CURRENT_DIR=$(cd "$(dirname "$0")";pwd)

echo "=========================================="
echo "Step 4: Setting up Claude configuration..."
echo "=========================================="
# 创建 ~/.claude 目录
mkdir -p ~/.claude

# 从 settings 文件夹复制配置文件
if [ -f "${CURRENT_DIR}/settings/claude.json" ]; then
    cp ${CURRENT_DIR}/settings/claude.json ~/.claude.json
    echo "Copied claude.json to ~/.claude.json"
fi

if [ -f "${CURRENT_DIR}/settings/projects.json" ]; then
    cp ${CURRENT_DIR}/settings/projects.json ~/.claude/projects.json
    echo "Copied projects.json to ~/.claude/projects.json"
fi

# 配置 settings
if [ -f "${CURRENT_DIR}/settings/settings.json" ]; then
    cp ${CURRENT_DIR}/settings/settings.json ~/.claude/settings.json
    echo "Copied settings.json to ~/.claude/settings.json"
fi
