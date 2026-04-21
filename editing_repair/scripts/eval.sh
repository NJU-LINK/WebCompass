#!/bin/bash
# Run editing or repair evaluation across both sp and mp page types in one go.
#
# Usage:   bash scripts/eval.sh <edit|repair>
# Env:
#   WEBCOMPASS_DATA_DIR  data root (contains edit/ and repair/);  default ./data
#   OUTPUT_DIR           results root;                            default ./results
#   MODEL                model id;                                default claude-sonnet-4-5-20250929
#   MODE                 text | image;                            default text
#   MAX_WORKERS / MAX_TOKENS / MAX_RETRY                          have sensible defaults
#
# Output layout:
#   ${OUTPUT_DIR}/${TASK}/${MODEL}_${MODE}_${TS}/{sp,mp}/${instance_id}/
set -euo pipefail

TASK="${1:-${TASK:-}}"
: "${TASK:?usage: bash scripts/eval.sh <edit|repair> (or export TASK)}"
case "$TASK" in
  edit|repair) ;;
  *) echo "TASK must be 'edit' or 'repair', got '$TASK'" >&2; exit 2 ;;
esac

TS="$(date +%Y%m%d_%H%M%S)"
DATA_DIR="${WEBCOMPASS_DATA_DIR:-./data}"
OUTPUT_DIR="${OUTPUT_DIR:-./results}"
MODEL="${MODEL:-claude-sonnet-4-5-20250929}"
MODE="${MODE:-text}"
MAX_WORKERS="${MAX_WORKERS:-16}"
MAX_TOKENS="${MAX_TOKENS:-$((1024*64))}"
MAX_RETRY="${MAX_RETRY:-12}"

mkdir -p log
SESSION="${MODEL}_${MODE}_${TS}"
LOG="log/eval-${TASK}-${SESSION}.log"
echo "Session: $SESSION"
echo "Log:     $LOG"

for PT in sp mp; do
  echo "==> ${PT}/${TASK}" | tee -a "$LOG"
  python -u eval.py \
    --base-path "${DATA_DIR}/${TASK}/${PT}" \
    --output-dir "${OUTPUT_DIR}/${TASK}" \
    --model "$MODEL" \
    --mode "$MODE" \
    --task "$TASK" \
    --max-workers "$MAX_WORKERS" \
    --max-tokens "$MAX_TOKENS" \
    --max-retry "$MAX_RETRY" \
    --timestamp "$TS" \
    >> "$LOG" 2>&1
done

echo "Done. Results in ${OUTPUT_DIR}/${TASK}/${SESSION}/{sp,mp}/"
