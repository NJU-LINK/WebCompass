# WebCompass 网页生成与评测

[English](README.md)

本模块提供完整的网页生成（Inference）与评测（Evaluation）流程。

## 环境要求

- Python 3.10+
- Docker（用于评测）
- ffmpeg（用于视频帧提取）

```bash
# 安装 ffmpeg（用于视频任务）
conda install -c conda-forge ffmpeg

# 安装 Python 依赖
pip install -e .
```

## 目录结构

```
generation/
├── inference/                 # 网页生成模块
│   ├── text_to_web.py        # 文本 → 网页
│   ├── image_to_web.py       # 图片 → 网页
│   └── video_to_web.py       # 视频 → 网页
├── evaluation/                # 评测模块
│   ├── agents/               # Docker Agent 配置
│   │   └── claude_code_web_coding/
│   ├── configs/              # 评测配置文件
│   ├── test.py               # Text/Video 评测入口
│   ├── test_image.py         # Image 评测入口
│   ├── judge_image.py        # Image LLM 评判（复刻质量）
│   └── evaluate.py           # 统一打分脚本
├── scripts/                   # 运行脚本
│   ├── run_text_inference.py
│   ├── run_image_inference.py
│   └── run_video_inference.py
├── call_model.py             # 模型 API 封装
├── model_client.py           # 模型客户端
├── prompts.py                # 提示词模板
└── utils.py                  # 工具函数
```

---

## 1. 网页生成（Inference）

### 1.1 环境变量

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选，默认 OpenAI
```

### 1.2 文本生成网页

从文本设计文档生成网页。

```bash
python -m generation.scripts.run_text_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o \
    --workers 4
```

**参数说明：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data` | 输入 JSONL 文件路径 | 必填 |
| `--output` | 输出目录 | 必填 |
| `--model` | 模型名称 | 必填 |
| `--base-url` | API Base URL | 从环境变量 |
| `--api-key` | API Key | 从环境变量 |
| `--workers` | 并行数 | 4 |
| `--max-retries` | 最大重试次数 | 3 |

### 1.3 图片生成网页

从参考截图生成网页。

```bash
python -m generation.scripts.run_image_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o \
    --workers 4
```

### 1.4 视频生成网页

从视频演示生成网页（自动提取关键帧）。

```bash
python -m generation.scripts.run_video_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o \
    --workers 4 \
    --fps 3.0 \
    --max-frames 30
```

**额外参数：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--fps` | 帧提取率 | 3.0 |
| `--max-frames` | 最大帧数 | 30 |

---

## 2. 网页评测

评测分为三步：**构建镜像 → 运行评测 → 算分**

### 2.1 构建 Docker 镜像

首次使用或更新 Agent 后需要重新构建：

```bash
cd generation/evaluation/agents/claude_code_web_coding
bash build_image.sh
```

### 2.2 配置文件

创建评测配置文件（JSON 格式）：

```json
{
    "tasks_file": "/path/to/tasks.jsonl",
    "agent_dir": "/path/to/WebCompass/generation/evaluation/agents/claude_code_web_coding",
    "output_dir": "/path/to/output",
    "existing_site_root": "/path/to/generated_sites",
    "start_index": 0,
    "end_index": 100,
    "num_tasks": -1,
    "num_processes": 4,
    "retry_count": 3,
    "anthropic_base_url": "https://api.anthropic.com/v1",
    "anthropic_auth_token": "YOUR_ANTHROPIC_API_KEY",
    "network_mode": "bridge",
    "model": "claude-sonnet-4-6"
}
```

**字段说明：**
| 字段 | 说明 |
|------|------|
| `tasks_file` | 任务文件路径（JSONL 格式） |
| `agent_dir` | Agent 目录路径 |
| `output_dir` | 评测输出目录（必须是绝对路径） |
| `existing_site_root` | 已生成网页的根目录 |
| `start_index` / `end_index` | 评测范围 |
| `num_tasks` | 评测任务数（-1 表示全部） |
| `num_processes` | 并行进程数 |
| `retry_count` | 失败重试次数 |
| `anthropic_auth_token` | Anthropic API Key |
| `model` | 使用的模型 |

### 2.3 Text/Video 评测流程

Text 和 Video 任务使用相同的评测脚本：

```bash
# 运行评测（Claude Code 会自动验证 checklist 并打分）
python -m generation.evaluation.test \
    --config /path/to/config.json \
    --models "model1,model2"

# 统一算分
python -m generation.evaluation.evaluate \
    --text_dir /path/to/text/results \
    --video_dir /path/to/video/results \
    --output_dir ./eval_output
```

### 2.4 Image 评测流程

Image 任务需要额外的 **LLM 评判步骤** 来评估设计质量：

```bash
# Step 1: 运行评测（生成网页截图）
python -m generation.evaluation.test_image \
    --config /path/to/config.json \
    --models "model1,model2"

# Step 2: LLM 评判（对比原图与生成图）
python -m generation.evaluation.judge_image \
    --root /path/to/image/results \
    --models model1 model2 \
    --model claude-opus-4-5-20250929 \
    --max-workers 4

# Step 3: 统一算分（从 checklist.json 读取 llm_score）
python -m generation.evaluation.evaluate \
    --image_dir /path/to/image/results \
    --output_dir ./eval_output
```

**judge_image.py 参数说明：**
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--root` | 包含模型结果的根目录 | 必填 |
| `--models` | 要评测的模型目录名 | 必填 |
| `--model` | 用于评判的多模态 LLM | claude-opus-4-5-20250929 |
| `--stream` | 流式输出模型响应 | False |
| `--max-workers` | 并发线程数 | 4 |
| `--summary` | 输出汇总 JSONL 路径 | None |

### 2.5 evaluate.py 参数说明

```bash
python -m generation.evaluation.evaluate [OPTIONS]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_dir` | Text 结果目录 | - |
| `--image_dir` | Image 结果目录 | - |
| `--video_dir` | Video 结果目录 | - |
| `--root` | 单一根目录（自动检测模态） | - |
| `--output_dir` | 输出目录 | `./eval_output` |
| `--quiet` | 抑制详细输出 | False |

---

## 3. 完整评测示例

### 3.1 Text 任务

```bash
# 1. 生成网页
python -m generation.scripts.run_text_inference \
    --data /path/to/text_tasks.jsonl \
    --output /path/to/output/text/ModelName \
    --model ModelName

# 2. 构建 Docker 镜像（仅首次）
bash generation/evaluation/agents/claude_code_web_coding/build_image.sh

# 3. 运行评测
python -m generation.evaluation.test \
    --config /path/to/text_config.json \
    --models "ModelName"

# 4. 统一算分
python -m generation.evaluation.evaluate \
    --text_dir /path/to/output/text/ModelName
```

### 3.2 Image 任务

```bash
# 1. 生成网页
python -m generation.scripts.run_image_inference \
    --data /path/to/image_tasks.jsonl \
    --output /path/to/output/image/ModelName \
    --model ModelName

# 2. 运行评测
python -m generation.evaluation.test_image \
    --config /path/to/image_config.json \
    --models "ModelName"

# 3. LLM 评判（设计质量必需步骤）
python -m generation.evaluation.judge_image \
    --root /path/to/output/image \
    --models ModelName \
    --model claude-opus-4-5-20250929

# 4. 统一算分
python -m generation.evaluation.evaluate \
    --image_dir /path/to/output/image/ModelName
```

### 3.3 Video 任务

```bash
# 1. 生成网页
python -m generation.scripts.run_video_inference \
    --data /path/to/video_tasks.jsonl \
    --output /path/to/output/video/ModelName \
    --model ModelName

# 2. 运行评测
python -m generation.evaluation.test \
    --config /path/to/video_config.json \
    --models "ModelName"

# 3. 统一算分
python -m generation.evaluation.evaluate \
    --video_dir /path/to/output/video/ModelName
```

---

## 4. 输出文件

### 4.1 生成阶段输出

```
output/
└── ModelName/
    └── {instance_id}/
        ├── index.html
        ├── styles.css
        ├── script.js
        ├── screenshots/      # 参考图片（Image 任务）
        ├── frames/           # 视频帧（Video 任务）
        └── .done             # 完成标记
```

### 4.2 评测阶段输出

```
output/
└── ModelName/
    └── {instance_id}/
        ├── task.json         # 任务配置
        ├── checklist.json    # 打分结果（Image 任务包含 llm_score）
        ├── image/            # 评测截图
        └── output_*/         # 每次运行的日志
```

### 4.3 算分输出

```
eval_output/
├── eval_results_{timestamp}.json   # 详细结果
└── eval_summary_{timestamp}.csv    # 汇总表格
```

---

## 5. 评测指标

| 指标 | 说明 |
|------|------|
| **Runnability** | 网页是否能正确加载和运行 |
| **Spec Implementation** | 功能是否符合需求 |
| **Design Quality** | 视觉设计是否符合参考（Image 任务使用 llm_score） |
| **Accuracy** | 总得分 / 最大分数 |
| **Harmonic Mean** | 各类别准确率的调和平均值 |

---

## 6. 常见问题

### Q1: Docker 镜像构建失败？
确保 Docker 已安装且有正确权限：
```bash
docker info
```
如果有网络问题，使用代理：
```bash
docker build \
    --build-arg http_proxy=http://your-proxy:port \
    --build-arg https_proxy=http://your-proxy:port \
    -f Dockerfile.web_coding \
    -t web_bench/base:latest .
```

### Q2: 评测卡住或超时？
- 检查 `num_processes` 是否过高
- 检查网络连接
- 查看 `output_*/` 目录下的日志

### Q3: checklist.json 中 score 为 null？
表示该条目未被验证。增加 `retry_count` 或手动检查原因。

### Q4: judge_image.py 报错？
- 检查 API Key 是否有效
- 确保 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 正确配置为多模态模型
- 检查 `screenshots/` 和 `image/` 目录是否包含图片

### Q5: evaluate.py 如何读取 LLM 评判分数？
对于 Image 任务，`judge_image.py` 会将 `llm_score` 写入 checklist.json。`evaluate.py` 同时读取 `score` 和 `llm_score` 字段 - 如果 `score` 为 null 但 `llm_score` 存在，则使用 `llm_score`，默认 `max_score` 为 100。
