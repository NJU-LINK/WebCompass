<p align="center">
<pre align="center">
<b>
  ██╗    ██╗███████╗██████╗  ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗ ███████╗███████╗
  ██║    ██║██╔════╝██╔══██╗██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗██╔════╝██╔════╝
  ██║ █╗ ██║█████╗  ██████╔╝██║     ██║   ██║██╔████╔██║██████╔╝███████║███████╗███████╗
  ██║███╗██║██╔══╝  ██╔══██╗██║     ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══██║╚════██║╚════██║
  ╚███╔███╔╝███████╗██████╔╝╚██████╗╚██████╔╝██║ ╚═╝ ██║██║     ██║  ██║███████║███████║
   ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝
</b>
</pre>
</p>

<p align="center">
  <a href="https://www.nju.edu.cn"><img src="site/public/figures/nju_logo.png" height="72" alt="Nanjing University"></a>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://huggingface.co/Kwaipilot"><img src="site/public/figures/kwaipilot_logo.png" height="72" alt="Kwaipilot"></a>
</p>
<p align="center">
  <b>NJU-LINK</b>&nbsp;&nbsp;×&nbsp;&nbsp;<b>Kwaipilot</b>
</p>

<h3 align="center">A Unified Multimodal Benchmark for Web Generation</h3>

<p align="center">
  <a href="https://arxiv.org/abs/2604.18224"><img src="https://img.shields.io/badge/arXiv-2604.18224-b31b1b.svg?style=for-the-badge" alt="arXiv"></a>
  <a href="https://nju-link.github.io/WebCompass/"><img src="https://img.shields.io/badge/docs-Project%20Page-blue.svg?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Docs"></a>
  <a href="https://huggingface.co/datasets/NJU-LINK/WebCompass"><img src="https://img.shields.io/badge/🤗-WebCompass-yellow.svg?style=for-the-badge" alt="Dataset"></a>
</p>
<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg?style=flat-square" alt="License"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#dataset">Dataset</a> &bull;
  <a href="#evaluation">Evaluation</a> &bull;
  <a href="#citation">Citation</a>
</p>

---

**WebCompass** is a unified multimodal benchmark and evaluation framework for assessing LLMs' ability to generate functional web pages from three types of inputs: text design documents, reference screenshots, and video demonstrations.

## Highlights

- **Multimodal Input Support**: Evaluate web generation from text, images, or videos
- **Five Task Types**: Text/Image/Video generation + Editing + Repair
- **Three-Dimension Evaluation**: Runnability, Spec Implementation, and Design Quality
- **LLM-as-Judge**: Visual comparison using multimodal LLMs (Gemini, GPT-4o, etc.)
- **Docker-based Evaluation**: Reproducible evaluation environment with Claude Code agent
- **Extensible Framework**: Easy integration of new models and agents

---

## Dataset

The dataset is hosted on HuggingFace: **[NJU-LINK/WebCompass](https://huggingface.co/datasets/NJU-LINK/WebCompass)**

### Download

```python
from datasets import load_dataset

# Generation tasks
ds_text  = load_dataset("NJU-LINK/WebCompass", "text-generation",  split="train")  # 123
ds_image = load_dataset("NJU-LINK/WebCompass", "image-generation", split="train")  # 116
ds_video = load_dataset("NJU-LINK/WebCompass", "video-generation", split="train")  # 94

# Editing tasks (single-page / multi-page splits, 150 each)
ds_edit_sp = load_dataset("NJU-LINK/WebCompass", "editing", split="sp")
ds_edit_mp = load_dataset("NJU-LINK/WebCompass", "editing", split="mp")

# Repair tasks (single-page / multi-page splits, 150 each)
ds_repair_sp = load_dataset("NJU-LINK/WebCompass", "repair", split="sp")
ds_repair_mp = load_dataset("NJU-LINK/WebCompass", "repair", split="mp")
```

### Dataset Structure

| Config             | Split   | Samples | Description |
|--------------------|---------|---------|-------------|
| `text-generation`  | train   | 123 | Generate from text design documents |
| `image-generation` | train   | 116 | Generate from reference screenshots |
| `video-generation` | train   | 94  | Generate from video demonstrations |
| `editing`          | sp / mp | 150 / 150 | Add features to a single- / multi-page site |
| `repair`           | sp / mp | 150 / 150 | Fix a broken single- / multi-page site to match a target |

### Data Format

Each task in the generation dataset is a JSON object with the following structure:

```json
{
  "instance_id": "106",
  "repo": "claude/webcoding",
  "base_commit": "main",
  "problem_statement": [
    {
      "task": "Verify page load and console errors",
      "category": "Runnability",
      "operation_sequence": "1. Open the homepage...",
      "expected_result": "The page loads completely...",
      "criteria": "Pass: No errors. Fail: Any blocking error...",
      "max_score": 10
    },
    {
      "task": "Check layout fidelity of the header section",
      "category": "Design Quality",
      "reference_image_path": "index.html.png",
      "max_score": 10
    }
  ],
  "meta": {
    "class": "image_generation",
    "difficulty": "N/A"
  }
}
```

**Categories:**
- `Runnability`: Page loads without errors (~10% weight)
- `Spec Implementation`: Interactions match specification (~60-70% weight)
- `Design Quality`: Visual fidelity to reference (~20-25% weight)

---

## Quick Start

### Installation

```bash
git clone https://github.com/NJU-LINK/WebCompass.git
cd WebCompass
pip install -e .

# For video tasks, install ffmpeg
conda install -c conda-forge ffmpeg

# For evaluation, install Docker
# https://docs.docker.com/engine/install/
```

### Dependencies

- Python 3.10+
- Docker (for evaluation)
- Node.js (for editing/repair tasks)
- ffmpeg (for video frame extraction)

### Configure LLM

WebCompass uses the OpenAI-compatible API format. Set environment variables for API access:

```bash
# For OpenAI
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_API_KEY="your-api-key"

# For other providers (e.g., Azure, local models)
export OPENAI_BASE_URL="https://your-api-endpoint/v1"
export OPENAI_API_KEY="your-api-key"
```

**Supported Models** (tested):
- OpenAI: `gpt-4o`, `gpt-4o-mini`, `o1`, `o3-mini`
- Anthropic: `claude-sonnet-4-5-20250929`, `claude-opus-4-5-20250929`
- Google: `gemini-2.5-pro-preview-05-06`, `gemini-2.5-flash-preview-04-17`
- Open-source: `Qwen3-VL-32B-Instruct`, `deepseek-chat`, etc.

```python
from generation.call_model import call_api

response = call_api("Hello, what model are you?", model="gpt-4o")
```

---

## Evaluation

WebCompass provides two types of evaluation:

1. **Generation Evaluation** (`generation/`) - Text/Image/Video to Web
2. **Editing & Repair Evaluation** (`editing_repair/`) - Code editing and bug fixing

### Generation Evaluation

See [generation/README.md](generation/README.md) for detailed instructions.

**Pipeline Overview:**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. Generate    │───▶│  2. Evaluate    │───▶│  3. LLM Judge   │───▶│  4. Score       │
│  (Inference)    │    │  (Docker Agent) │    │  (Image only)   │    │  (Calculate)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Quick Overview

```bash
# 1. Build Docker image (first time only)
cd generation/evaluation/agents/claude_code_web_coding
bash build_image.sh

# 2. Generate web pages
python -m generation.scripts.run_text_inference \
    --data /path/to/tasks.jsonl \
    --output /path/to/output \
    --model gpt-4o

# 3. Run evaluation (Claude Code agent verifies checklist)
python -m generation.evaluation.test \
    --config generation/evaluation/configs/your_config.json \
    --models "ModelName"

# 4. For image tasks: run LLM judge first (required for Design Quality)
python -m generation.evaluation.judge_image \
    --root /path/to/image/results \
    --models ModelName \
    --model claude-opus-4-5-20250929

# 5. Calculate scores
python -m generation.evaluation.evaluate \
    --root /path/to/results \
    --output_dir ./eval_output
```

### Editing & Repair Evaluation

See [editing_repair/README.md](editing_repair/README.md) for detailed instructions.

**Task Types:**
- **Editing**: Add new features to an existing website based on instructions
- **Repair**: Fix bugs in a broken website to match the target behavior

#### Quick Overview

```bash
cd editing_repair

# Download data from HuggingFace
python scripts/download_from_hf.py --out-root ./data

# Set environment variables
export TASK=edit                    # edit | repair
export WEBCOMPASS_DATA_DIR=./data
export OUTPUT_DIR=./results
export MODEL=claude-sonnet-4-5-20250929
export MODE=text                    # text | image

# Run evaluation
bash scripts/eval.sh

# Judge results
export SESSION_NAME=$(ls -t "${OUTPUT_DIR}/${TASK}" | head -1)
export JUDGE_MODEL=claude-opus-4-5-20250929
bash scripts/judge.sh
```

### Evaluation Dimensions

#### Generation Tasks

| Dimension | Description | Weight |
|-----------|-------------|--------|
| **Runnability** | Page loads without errors | ~10% |
| **Spec Implementation** | Interactions match specification | ~60-70% |
| **Design Quality** | Visual fidelity and layout accuracy | ~20-25% |

#### Editing & Repair Tasks

| Task   | Dim 1                  | Dim 2                  | Dim 3                |
|--------|------------------------|------------------------|----------------------|
| Edit   | instruction_targeting  | feature_integrity      | style_conformance    |
| Repair | root_cause_targeting   | interaction_integrity  | reference_fidelity   |

---

## Project Structure

```
WebCompass/
├── site/                           # Project website (Next.js)
├── generation/                     # Generation evaluation framework
│   ├── call_model.py               # Unified model client
│   ├── inference/                  # Web generation scripts
│   │   ├── text_to_web.py
│   │   ├── image_to_web.py
│   │   └── video_to_web.py
│   ├── evaluation/                 # Evaluation tools
│   │   ├── agents/                 # Agent implementations
│   │   │   └── claude_code_web_coding/
│   │   ├── configs/                # Configuration files
│   │   ├── test.py                 # Text/Video evaluation
│   │   ├── test_image.py           # Image evaluation
│   │   ├── judge_image.py          # LLM visual judge
│   │   └── evaluate.py             # Score calculation
│   └── scripts/                    # CLI scripts
├── editing_repair/                 # Editing & Repair evaluation
│   ├── eval.py                     # Main evaluation script
│   ├── judge.py                    # LLM judge
│   ├── scripts/                    # Helper scripts
│   └── README.md
├── requirements.txt
├── setup.py
└── README.md
```

---

## Citation

If you use WebCompass in your research, please cite:

```bibtex
@misc{lei2026webcompassmultimodalwebcoding,
      title={WebCompass: Towards Multimodal Web Coding Evaluation for Code Language Models}, 
      author={Xinping Lei and Xinyu Che and Junqi Xiong and Chenchen Zhang and Yukai Huang and Chenyu Zhou and Haoyang Huang and Minghao Liu and Letian Zhu and Hongyi Ye and Jinhua Hao and Ken Deng and Zizheng Zhan and Han Li and Dailin Li and Yifan Yao and Ming Sun and Zhaoxiang Zhang and Jiaheng Liu},
      year={2026},
      eprint={2604.18224},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2604.18224}, 
}
```

## License

This project is licensed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built at <a href="https://www.nju.edu.cn">Nanjing University</a> &amp; <a href="https://huggingface.co/Kwaipilot">Kwaipilot</a></sub>
</p>
