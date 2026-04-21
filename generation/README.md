# WebCompass Generation & Evaluation

[中文版](README_CN.md)

This module provides a complete pipeline for web page generation (Inference) and evaluation (Evaluation).

## Prerequisites

- Python 3.10+
- Docker (for evaluation)
- ffmpeg (for video frame extraction)

```bash
# Install ffmpeg (for video tasks)
conda install -c conda-forge ffmpeg

# Install Python dependencies
pip install -e .
```

## Directory Structure

```
generation/
├── inference/                 # Web generation module
│   ├── text_to_web.py        # Text → Web
│   ├── image_to_web.py       # Image → Web
│   └── video_to_web.py       # Video → Web
├── evaluation/                # Evaluation module
│   ├── agents/               # Docker Agent configurations
│   │   └── claude_code_web_coding/
│   ├── configs/              # Evaluation config files
│   ├── test.py               # Text/Video evaluation entry
│   ├── test_image.py         # Image evaluation entry
│   ├── judge_image.py        # Image LLM judge (replication quality)
│   └── evaluate.py           # Unified scoring script
├── scripts/                   # Runner scripts
│   ├── run_text_inference.py
│   ├── run_image_inference.py
│   └── run_video_inference.py
├── call_model.py             # Model API wrapper
├── model_client.py           # Model client
├── prompts.py                # Prompt templates
└── utils.py                  # Utility functions
```

---

## 1. Web Generation (Inference)

### 1.1 Environment Variables

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional, defaults to OpenAI
```

### 1.2 Text-to-Web

Generate web pages from text design documents.

```bash
python -m generation.scripts.run_text_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o \
    --workers 4
```

**Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--data` | Input JSONL file path | Required |
| `--output` | Output directory | Required |
| `--model` | Model name | Required |
| `--base-url` | API Base URL | From env |
| `--api-key` | API Key | From env |
| `--workers` | Parallelism | 4 |
| `--max-retries` | Max retry attempts | 3 |

### 1.3 Image-to-Web

Generate web pages from reference screenshots.

```bash
python -m generation.scripts.run_image_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o \
    --workers 4
```

### 1.4 Video-to-Web

Generate web pages from video demonstrations (automatically extracts key frames).

```bash
python -m generation.scripts.run_video_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o \
    --workers 4 \
    --fps 3.0 \
    --max-frames 30
```

**Additional Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--fps` | Frame extraction rate | 3.0 |
| `--max-frames` | Maximum frames | 30 |

---

## 2. Web Evaluation

Evaluation consists of three steps: **Build Image → Run Evaluation → Score**

### 2.1 Build Docker Image

Required on first use or after Agent updates:

```bash
cd generation/evaluation/agents/claude_code_web_coding
bash build_image.sh
```

### 2.2 Configuration File

Create an evaluation config file (JSON format):

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

**Field Descriptions:**
| Field | Description |
|-------|-------------|
| `tasks_file` | Task file path (JSONL format) |
| `agent_dir` | Agent directory path |
| `output_dir` | Evaluation output directory (must be absolute path) |
| `existing_site_root` | Root directory of generated websites |
| `start_index` / `end_index` | Evaluation range |
| `num_tasks` | Number of tasks (-1 for all) |
| `num_processes` | Parallel processes |
| `retry_count` | Retry count on failure |
| `anthropic_auth_token` | Anthropic API Key |
| `model` | Model to use |

### 2.3 Text/Video Evaluation Pipeline

Text and Video tasks use the same evaluation script:

```bash
# Run evaluation (Claude Code auto-verifies checklist and scores)
python -m generation.evaluation.test \
    --config /path/to/config.json \
    --models "model1,model2"

# Calculate scores
python -m generation.evaluation.evaluate \
    --text_dir /path/to/text/results \
    --video_dir /path/to/video/results \
    --output_dir ./eval_output
```

### 2.4 Image Evaluation Pipeline

Image tasks require an additional **LLM judging step** for Design Quality scoring:

```bash
# Step 1: Run evaluation (generate webpage screenshots)
python -m generation.evaluation.test_image \
    --config /path/to/config.json \
    --models "model1,model2"

# Step 2: LLM Judge (compare reference vs generated images)
python -m generation.evaluation.judge_image \
    --root /path/to/image/results \
    --models model1 model2 \
    --model claude-opus-4-5-20250929 \
    --max-workers 4

# Step 3: Calculate scores (reads llm_score from checklist.json)
python -m generation.evaluation.evaluate \
    --image_dir /path/to/image/results \
    --output_dir ./eval_output
```

**judge_image.py Parameters:**
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--root` | Root directory containing model results | Required |
| `--models` | Model directory names to evaluate | Required |
| `--model` | Multimodal LLM for judging | claude-opus-4-5-20250929 |
| `--stream` | Stream model output | False |
| `--max-workers` | Concurrent threads | 4 |
| `--summary` | Output summary JSONL path | None |

### 2.5 evaluate.py Parameters

```bash
python -m generation.evaluation.evaluate [OPTIONS]
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--text_dir` | Text results directory | - |
| `--image_dir` | Image results directory | - |
| `--video_dir` | Video results directory | - |
| `--root` | Single root directory (auto-detect modality) | - |
| `--output_dir` | Output directory | `./eval_output` |
| `--quiet` | Suppress detailed output | False |

---

## 3. Complete Evaluation Examples

### 3.1 Text Tasks

```bash
# 1. Generate web pages
python -m generation.scripts.run_text_inference \
    --data /path/to/text_tasks.jsonl \
    --output /path/to/output/text/ModelName \
    --model ModelName

# 2. Build Docker image (first time only)
bash generation/evaluation/agents/claude_code_web_coding/build_image.sh

# 3. Run evaluation
python -m generation.evaluation.test \
    --config /path/to/text_config.json \
    --models "ModelName"

# 4. Calculate scores
python -m generation.evaluation.evaluate \
    --text_dir /path/to/output/text/ModelName
```

### 3.2 Image Tasks

```bash
# 1. Generate web pages
python -m generation.scripts.run_image_inference \
    --data /path/to/image_tasks.jsonl \
    --output /path/to/output/image/ModelName \
    --model ModelName

# 2. Run evaluation
python -m generation.evaluation.test_image \
    --config /path/to/image_config.json \
    --models "ModelName"

# 3. LLM Judge (required step for Design Quality)
python -m generation.evaluation.judge_image \
    --root /path/to/output/image \
    --models ModelName \
    --model claude-opus-4-5-20250929

# 4. Calculate scores
python -m generation.evaluation.evaluate \
    --image_dir /path/to/output/image/ModelName
```

### 3.3 Video Tasks

```bash
# 1. Generate web pages
python -m generation.scripts.run_video_inference \
    --data /path/to/video_tasks.jsonl \
    --output /path/to/output/video/ModelName \
    --model ModelName

# 2. Run evaluation
python -m generation.evaluation.test \
    --config /path/to/video_config.json \
    --models "ModelName"

# 3. Calculate scores
python -m generation.evaluation.evaluate \
    --video_dir /path/to/output/video/ModelName
```

---

## 4. Output Files

### 4.1 Generation Phase Output

```
output/
└── ModelName/
    └── {instance_id}/
        ├── index.html
        ├── styles.css
        ├── script.js
        ├── screenshots/      # Reference images (Image tasks)
        ├── frames/           # Video frames (Video tasks)
        └── .done             # Completion marker
```

### 4.2 Evaluation Phase Output

```
output/
└── ModelName/
    └── {instance_id}/
        ├── task.json         # Task configuration
        ├── checklist.json    # Scoring results (includes llm_score for image tasks)
        ├── image/            # Evaluation screenshots
        └── output_*/         # Logs for each run
```

### 4.3 Scoring Output

```
eval_output/
├── eval_results_{timestamp}.json   # Detailed results
└── eval_summary_{timestamp}.csv    # Summary table
```

---

## 5. Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **Runnability** | Whether the webpage loads and runs correctly |
| **Spec Implementation** | Whether functionality matches requirements |
| **Design Quality** | Whether visual design matches the reference (uses llm_score for image tasks) |
| **Accuracy** | Total score / Maximum score |
| **Harmonic Mean** | Harmonic mean of accuracy across categories |

---

## 6. FAQ

### Q1: Docker image build fails?
Ensure Docker is installed and you have proper permissions:
```bash
docker info
```
If network issues occur, use proxy:
```bash
docker build \
    --build-arg http_proxy=http://your-proxy:port \
    --build-arg https_proxy=http://your-proxy:port \
    -f Dockerfile.web_coding \
    -t web_bench/base:latest .
```

### Q2: Evaluation hangs or times out?
- Check if `num_processes` is too high
- Check network connectivity
- Check logs in `output_*/` directories

### Q3: checklist.json has score as null?
This means the item was not verified. Increase `retry_count` or manually check the cause.

### Q4: judge_image.py errors?
- Check if the API Key is valid
- Ensure `OPENAI_API_KEY` and `OPENAI_BASE_URL` are set correctly for your multimodal model
- Check if `screenshots/` and `image/` directories contain images

### Q5: How does evaluate.py read LLM judge scores?
For image tasks, `judge_image.py` writes `llm_score` to checklist.json. `evaluate.py` reads both `score` and `llm_score` fields - if `score` is null but `llm_score` exists, it uses `llm_score` with a default `max_score` of 100.
