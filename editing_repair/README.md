# WebCompass — Editing & Repair

Code for the **editing** and **repair** halves of the WebCompass benchmark.
The dataset is hosted on HuggingFace at [NJU-LINK/WebCompass](https://huggingface.co/datasets/NJU-LINK/WebCompass) under the `editing` and `repair` configs (each with `sp` and `mp` splits — single-page and multi-page sites; 150 cases per split, 600 total).

## Setup

```bash
# Node.js for any web rendering / Playwright steps
conda install -c conda-forge nodejs
# Python deps (from the repo root)
pip install -e .
```

API credentials — set environment variables (same scheme as `generation/`'s evaluator):

```bash
export OPENAI_BASE_URL="https://your-api-host/v1"
export OPENAI_API_KEY="sk-..."
```

`OPENAI_BASE_URL` defaults to `https://api.openai.com/v1` if unset.

## Get the data

```bash
cd editing_repair
# Download editing/ + repair/ from HF and reconstruct the local layout
# eval.py expects:  ./data/{edit,repair}/{sp,mp}/{instance_id}/{info.json,src/,dst/}
python scripts/download_from_hf.py --out-root ./data
# Pass --copy if you don't want symlinks into the HF cache
```

After this, `./data/edit/sp/<id>/info.json` etc. are ready for the evaluator.

## Run evaluation

All evaluation is organised **per task** (`edit` or `repair`); a single
invocation walks both `sp` and `mp`. `TASK` and everything else are read
from env vars — `export` them once, then call the scripts.

```bash
# one-time config
export TASK=edit                    # edit | repair
export WEBCOMPASS_DATA_DIR=./data   # data root (contains edit/ and repair/)
export OUTPUT_DIR=./results         # results root
export MODEL=claude-sonnet-4-5-20250929
export MODE=text                    # text | image

# 1) generate model answers → ./results/edit/<MODEL>_<MODE>_<TS>/{sp,mp}/<id>/
bash scripts/eval.sh

# 2) judge a session
export SESSION_NAME=$(ls -t "${OUTPUT_DIR}/${TASK}" | head -1)
export JUDGE_MODEL=gemini-3-flash-preview
bash scripts/judge.sh

# 3) continue a partially-completed eval
bash scripts/eval_continue.sh       # reuses $SESSION_NAME
```

Other env vars (all have defaults — see the script headers):
`MAX_WORKERS`, `MAX_TOKENS`, `MAX_RETRY`, `OUTPUT_FILENAME`.
`TASK` also accepts a positional arg: `bash scripts/eval.sh edit`.

## Dataset structure (after `download_from_hf.py`)

```
data/
├── edit/
│   ├── sp/<instance_id>/
│   │   ├── info.json          # task description + src_code text + screenshot refs
│   │   └── src/               # screenshots + binary resources
│   └── mp/<instance_id>/...
└── repair/
    ├── sp/<instance_id>/
    │   ├── info.json
    │   ├── src/               # broken page assets
    │   └── dst/               # target screenshots
    └── mp/<instance_id>/...
```

## Judge rubric

Each generated answer is scored on three dimensions (0-10 each; see paper §F.5):

| Task   | Dim 1                  | Dim 2                  | Dim 3                |
|--------|------------------------|------------------------|----------------------|
| edit   | instruction_targeting  | feature_integrity      | style_conformance    |
| repair | root_cause_targeting   | interaction_integrity  | reference_fidelity   |

`utils/stat_uitils.py` aggregates per-task / per-difficulty harmonic means from `judge.json`; open `stat_result.ipynb` or `stat_result_sp_mp.ipynb` for a template.
