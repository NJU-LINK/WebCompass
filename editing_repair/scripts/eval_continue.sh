#!/bin/bash
# Continue an interrupted eval session: only re-runs cases without an info.json.
#
# Usage:   bash scripts/eval_continue.sh <edit|repair>
# Env:
#   WEBCOMPASS_DATA_DIR  data root (contains edit/ and repair/);  default ./data
#   OUTPUT_DIR           results root used at eval time;          default ./results
#   SESSION_NAME         the model_mode_TS folder, REQUIRED
#                        (e.g. claude-sonnet-4-5-20250929_text_20260118_120000)
set -euo pipefail

TASK="${1:-${TASK:-}}"
: "${TASK:?usage: bash scripts/eval_continue.sh <edit|repair> (or export TASK)}"
case "$TASK" in
  edit|repair) ;;
  *) echo "TASK must be 'edit' or 'repair', got '$TASK'" >&2; exit 2 ;;
esac

TS="$(date +%Y%m%d_%H%M%S)"
DATA_DIR="${WEBCOMPASS_DATA_DIR:-./data}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"
SESSION_NAME="${SESSION_NAME:?Set SESSION_NAME to the eval session folder to continue}"
MAX_WORKERS="${MAX_WORKERS:-16}"
MAX_TOKENS="${MAX_TOKENS:-$((1024*64))}"
MAX_RETRY="${MAX_RETRY:-12}"

mkdir -p log
LOG="log/continue-${TASK}-${SESSION_NAME}-${TS}.log"
echo "Log: $LOG"

for PT in sp mp; do
  RESULTS_PATH="${OUTPUT_DIR}/${TASK}/${SESSION_NAME}"
  if [ ! -d "${RESULTS_PATH}/${PT}" ]; then
    echo "Skip ${PT}: ${RESULTS_PATH}/${PT} does not exist" | tee -a "$LOG"
    continue
  fi
  echo "==> ${PT}: continuing ${RESULTS_PATH}/${PT}" | tee -a "$LOG"
  python -u eval.py \
    --base-path "${DATA_DIR}/${TASK}/${PT}" \
    --output-dir "${OUTPUT_DIR}/${TASK}" \
    --task "$TASK" \
    --max-workers "$MAX_WORKERS" \
    --max-tokens "$MAX_TOKENS" \
    --max-retry "$MAX_RETRY" \
    --model-result-path "$RESULTS_PATH" \
    >> "$LOG" 2>&1
done

echo "Done."
