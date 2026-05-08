#!/usr/bin/env bash
# Bootstrap for 31B Dense run on a RunPod pod.
#
# Expects to be run from /workspace after `runpodctl receive` has dropped
# project.tar.gz here. Also expects these env vars set on pod creation:
#   HUGGINGFACE_TOKEN, HF_TOKEN (same value), ANTHROPIC_API_KEY
#
# Usage on pod:
#   cd /workspace
#   tar xzf project.tar.gz
#   bash bootstrap.sh

set -euo pipefail

# RunPod injects pod-create env vars into /etc/rp_environment, not into SSH sessions.
set -a; source /etc/rp_environment 2>/dev/null || true; set +a

# Disable HF's xet/hf_transfer fast downloaders — they fail intermittently with
# "Internal Writer Error: Failed to send data: receiver dropped" on big shards.
# Plain HTTP is slower but reliable.
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
unset HF_XET_HIGH_PERFORMANCE 2>/dev/null || true

cd /workspace

echo "──────────────────────────────────────────────────────────────"
echo " 31B Dense pipeline bootstrap"
echo " $(date -u +%FT%TZ)"
echo "──────────────────────────────────────────────────────────────"

# ── 1. GPU sanity ────────────────────────────────────────────────────────
echo "[1/6] GPU check"
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
echo

# ── 2. Env var sanity (fail fast before downloading 16GB) ────────────────
echo "[2/6] Env vars"
: "${HUGGINGFACE_TOKEN:?HUGGINGFACE_TOKEN missing — pass via --env on pod create}"
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY missing — pass via --env on pod create}"
# HF SDK looks for HF_TOKEN / HUGGINGFACE_HUB_TOKEN
export HF_TOKEN="${HF_TOKEN:-$HUGGINGFACE_TOKEN}"
export HUGGINGFACE_HUB_TOKEN="$HF_TOKEN"
echo "  HUGGINGFACE_TOKEN  set (len=${#HUGGINGFACE_TOKEN})"
echo "  ANTHROPIC_API_KEY  set (len=${#ANTHROPIC_API_KEY})"
echo

# ── 3. Python deps ───────────────────────────────────────────────────────
echo "[3/6] Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  done"
echo

# ── 4. HF gated-model access check ───────────────────────────────────────
echo "[4/6] Checking HF access to google/gemma-4-31B-it"
python - <<'PY'
import os, sys
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HUGGINGFACE_TOKEN"])
for repo in ["google/gemma-4-31B-it", "huihui-ai/Huihui-gemma-4-31B-it-abliterated"]:
    try:
        api.model_info(repo)
        print(f"  ✓ {repo}")
    except Exception as e:
        print(f"  ✗ {repo}: {e}")
        sys.exit(1)
PY
echo

# ── 5. Run pipeline ──────────────────────────────────────────────────────
echo "[5/6] Running pipeline (--size 31b)"
echo
echo "  Monitor from another SSH session:"
echo "    tail -f /workspace/run.log               # full stdout (banner + tqdm)"
echo "    tail -f /workspace/logs/31b_*.log        # structured per-phase log"
echo "    cat    /workspace/data/outputs/compliance_rates.csv  # current results"
echo
echo "  If you didn't already wrap with nohup, kill this and re-run as:"
echo "    nohup bash bootstrap.sh > /workspace/run.log 2>&1 &"
echo "    echo \$! > /workspace/run.pid; tail -f /workspace/run.log"
echo
mkdir -p logs

# Allow pipeline to fail without aborting the script — we still want to
# bundle whatever partial results exist for debugging.
set +e
python scripts/run_pipeline.py --size 31b
PIPELINE_EXIT=$?
set -e
echo "Pipeline exit code: $PIPELINE_EXIT"
echo

# ── 6. Bundle results for sync back ──────────────────────────────────────
echo "[6/6] Bundling results (always — even on partial failure)"
RESULTS=/workspace/results_31b_$(date -u +%Y%m%d_%H%M%S).tar.gz
tar -czf "$RESULTS" data/outputs logs 2>/dev/null || true
ls -lh "$RESULTS"
echo
echo "──────────────────────────────────────────────────────────────"
if [ "$PIPELINE_EXIT" = "0" ]; then
  echo " ✓ DONE. From the pod:"
else
  echo " ✗ Pipeline failed (exit=$PIPELINE_EXIT) — bundle has partial results."
  echo "   From the pod:"
fi
echo "    runpodctl send $RESULTS"
echo " then on the laptop:"
echo "    runpodctl receive <code>"
echo "──────────────────────────────────────────────────────────────"
exit "$PIPELINE_EXIT"
