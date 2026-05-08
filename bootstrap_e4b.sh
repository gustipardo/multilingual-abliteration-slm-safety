#!/usr/bin/env bash
# Bootstrap for E4B run on a RunPod pod (unattended overnight).
#
# Differs from bootstrap.sh (the 31B version):
#   - Targets E4B
#   - Skips mechanistic phase (--skip-mechanistic)
#   - Uploads results to a private HuggingFace dataset (no laptop needed for sync)
#   - Self-terminates the pod when finished (success OR failure)
#   - 8-hour watchdog hard-kill in case the pipeline hangs
#
# Required env vars (pass via --env on pod create):
#   HUGGINGFACE_TOKEN, ANTHROPIC_API_KEY, RUNPOD_API_KEY
# RUNPOD_POD_ID is auto-injected by RunPod.
#
# Usage on pod:
#   cd /workspace && tar xzf project.tar.gz
#   nohup bash bootstrap_e4b.sh > /workspace/run.log 2>&1 &

set -uo pipefail   # NOT -e: we want to reach the cleanup section even on failure

# RunPod pod-create env vars land in /etc/rp_environment, not in SSH sessions.
set -a; source /etc/rp_environment 2>/dev/null || true; set +a

# Disable HF parallel downloaders (xet/hf_transfer crash on big shards).
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
unset HF_XET_HIGH_PERFORMANCE 2>/dev/null || true

cd /workspace

echo "──────────────────────────────────────────────────────────────"
echo " E4B unattended pipeline bootstrap"
echo " $(date -u +%FT%TZ)  pod=${RUNPOD_POD_ID:-?}"
echo "──────────────────────────────────────────────────────────────"

# ── 1. Install runpodctl on pod (needed for self-terminate) ──────────────
echo "[1/8] Installing runpodctl"
if ! command -v runpodctl &>/dev/null; then
  curl -sSL https://cli.runpod.net | bash
fi
export PATH="$HOME/.local/bin:$PATH"
mkdir -p "$HOME/.runpod"
cat > "$HOME/.runpod/config.toml" <<EOF
apiKey = "${RUNPOD_API_KEY:-}"
EOF
runpodctl version
echo

# ── 2. Watchdog: hard-terminate after 8h regardless ──────────────────────
echo "[2/8] Arming 8h watchdog"
(
  sleep 28800
  echo "[WATCHDOG] 8h timeout reached, force-deleting pod $RUNPOD_POD_ID"
  runpodctl pod delete "$RUNPOD_POD_ID" || true
) &
WATCHDOG_PID=$!
echo "  watchdog PID: $WATCHDOG_PID"
echo

# ── 3. GPU sanity ────────────────────────────────────────────────────────
echo "[3/8] GPU check"
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
echo

# ── 4. Env var sanity (fail fast before downloading) ─────────────────────
echo "[4/8] Env vars"
: "${HUGGINGFACE_TOKEN:?HUGGINGFACE_TOKEN missing}"
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY missing}"
: "${RUNPOD_API_KEY:?RUNPOD_API_KEY missing}"
: "${RUNPOD_POD_ID:?RUNPOD_POD_ID missing}"
export HF_TOKEN="${HF_TOKEN:-$HUGGINGFACE_TOKEN}"
export HUGGINGFACE_HUB_TOKEN="$HF_TOKEN"
echo "  all required tokens present"
echo

# ── 5. Python deps ───────────────────────────────────────────────────────
echo "[5/8] Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet huggingface_hub
echo "  done"
echo

# ── 6. HF gated-model access check ───────────────────────────────────────
echo "[6/8] Checking HF access to E4B models"
python - <<'PY'
import os, sys
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HUGGINGFACE_TOKEN"])
for repo in ["google/gemma-4-E4B-it", "huihui-ai/Huihui-gemma-4-E4B-it-abliterated"]:
    try:
        api.model_info(repo)
        print(f"  ✓ {repo}")
    except Exception as e:
        print(f"  ✗ {repo}: {e}")
        sys.exit(1)
PY
echo

# ── 7. Run pipeline (E4B, skip mechanistic) ──────────────────────────────
echo "[7/8] Running pipeline (--size e4b --skip-mechanistic)"
mkdir -p logs
set +e
python scripts/run_pipeline.py --size e4b --skip-mechanistic
PIPELINE_EXIT=$?
set -e
echo "Pipeline exit code: $PIPELINE_EXIT"
echo

# ── 8. Bundle + upload + self-terminate (always runs) ────────────────────
echo "[8/8] Bundling and uploading results"
TS=$(date -u +%Y%m%d_%H%M%S)
RESULTS="/workspace/results_e4b_${TS}.tar.gz"
tar -czf "$RESULTS" data/outputs logs 2>/dev/null || true
ls -lh "$RESULTS" || true

python - <<PY
import os, sys
from huggingface_hub import HfApi, create_repo
token = os.environ["HUGGINGFACE_TOKEN"]
api = HfApi(token=token)
user = api.whoami()["name"]
repo_id = f"{user}/abliteration-e4b-results"
try:
    create_repo(repo_id, repo_type="dataset", private=True, token=token, exist_ok=True)
    print(f"  repo ready: {repo_id}")
except Exception as e:
    print(f"  create_repo: {e}")
try:
    url = api.upload_file(
        path_or_fileobj="$RESULTS",
        path_in_repo="results_e4b_${TS}.tar.gz",
        repo_id=repo_id,
        repo_type="dataset",
    )
    print(f"  ✓ uploaded: {url}")
except Exception as e:
    print(f"  ✗ upload failed: {e}")
    sys.exit(2)
PY
UPLOAD_EXIT=$?
echo "Upload exit code: $UPLOAD_EXIT"
echo

kill "$WATCHDOG_PID" 2>/dev/null || true

echo "──────────────────────────────────────────────────────────────"
if [ "$PIPELINE_EXIT" = "0" ] && [ "$UPLOAD_EXIT" = "0" ]; then
  echo " ✓ DONE — pipeline OK, results uploaded. Self-terminating."
else
  echo " ✗ pipeline_exit=$PIPELINE_EXIT upload_exit=$UPLOAD_EXIT"
  echo "   Self-terminating anyway (whatever was uploaded is the bundle)."
fi
echo "──────────────────────────────────────────────────────────────"

# Self-terminate (this is the last instruction; whatever happens after, the pod is gone)
runpodctl pod delete "$RUNPOD_POD_ID"
