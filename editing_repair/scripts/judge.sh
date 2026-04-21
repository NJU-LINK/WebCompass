#!/bin/bash
# Judge an existing eval session for editing or repair (sp + mp combined).
#
# Usage:   bash scripts/judge.sh <edit|repair>
# Env:
#   WEBCOMPASS_DATA_DIR  data root (contains edit/ and repair/);  default ./data
#   OUTPUT_DIR           results root used at eval time;          default ./results
#   SESSION_NAME         the model_mode_TS folder, REQUIRED
#                        (e.g. claude-sonnet-4-5-20250929_text_20260118_120000)
#   JUDGE_MODEL                                                   default gemini-3-flash-preview
#   OUTPUT_FILENAME                                               default judge.json
set -euo pipefail

TASK="${1:-${TASK:-}}"
: "${TASK:?usage: bash scripts/judge.sh <edit|repair> (or export TASK)}"
case "$TASK" in
  edit|repair) ;;
  *) echo "TASK must be 'edit' or 'repair', got '$TASK'" >&2; exit 2 ;;
esac

TS="$(date +%Y%m%d_%H%M%S)"
DATA_DIR="${WEBCOMPASS_DATA_DIR:-./data}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"
SESSION_NAME="${SESSION_NAME:?Set SESSION_NAME to the eval session folder name}"
JUDGE_MODEL="${JUDGE_MODEL:-gemini-3-flash-preview}"
MAX_WORKERS="${MAX_WORKERS:-16}"
MAX_TOKENS="${MAX_TOKENS:-$((32*1024))}"
MAX_RETRY="${MAX_RETRY:-6}"
OUTPUT_FILENAME="${OUTPUT_FILENAME:-judge.json}"

mkdir -p log
LOG="log/judge-${TASK}-${SESSION_NAME}-by-${JUDGE_MODEL}-${TS}.log"
echo "Log: $LOG"

for PT in sp mp; do
  RESULTS_PATH="${OUTPUT_DIR}/${TASK}/${SESSION_NAME}/${PT}"
  if [ ! -d "$RESULTS_PATH" ]; then
    echo "Skip ${PT}: $RESULTS_PATH does not exist" | tee -a "$LOG"
    continue
  fi
  echo "==> ${PT}: $RESULTS_PATH" | tee -a "$LOG"
  python -u judge.py \
    --base-data-path "${DATA_DIR}/${TASK}/${PT}" \
    --results-path "$RESULTS_PATH" \
    --model "$JUDGE_MODEL" \
    --task "$TASK" \
    --max-workers "$MAX_WORKERS" \
    --max-tokens "$MAX_TOKENS" \
    --max-retry "$MAX_RETRY" \
    --output-filename "$OUTPUT_FILENAME" \
    >> "$LOG" 2>&1
done

echo "Done. Judge files: ${OUTPUT_DIR}/${TASK}/${SESSION_NAME}/{sp,mp}/<id>/${OUTPUT_FILENAME}"
