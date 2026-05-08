#!/usr/bin/env bash
# Bootstrap for E2B run on a RunPod pod (unattended).
#
# Differs from bootstrap_e4b.sh:
#   - Targets E2B (E2B in 4-bit ~2GB VRAM, much faster than E4B)
#   - Uploads results to abliteration-e2b-results private HF dataset
#   - Self-terminate uses GraphQL curl (the curl-installed runpodctl lacks `pod` subcommand;
#     this was the cause of E4B pod overage on 2026-05-05)
#   - 8h watchdog (E2B with abliterated runs to max_new_tokens=512 takes ~7-8h)
#   - Incremental HF uploader every 60s (so a crash bounds data loss to <60s)
#
# Required env vars (pass via --env on pod create):
#   HUGGINGFACE_TOKEN, ANTHROPIC_API_KEY, RUNPOD_API_KEY
# RUNPOD_POD_ID is auto-injected by RunPod.
#
# Usage on pod:
#   cd /workspace && tar xzf project.tar.gz
#   nohup bash bootstrap_e2b.sh > /workspace/run.log 2>&1 &

set -uo pipefail   # NOT -e: we want to reach the cleanup section even on failure

# RunPod pod-create env vars land in /etc/rp_environment, not in SSH sessions.
set -a; source /etc/rp_environment 2>/dev/null || true; set +a

# Disable HF parallel downloaders (xet/hf_transfer crash on big shards).
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
unset HF_XET_HIGH_PERFORMANCE 2>/dev/null || true

cd /workspace

echo "──────────────────────────────────────────────────────────────"
echo " E2B unattended pipeline bootstrap"
echo " $(date -u +%FT%TZ)  pod=${RUNPOD_POD_ID:-?}"
echo "──────────────────────────────────────────────────────────────"

# Self-terminate helper: GraphQL podTerminate mutation.
# The curl-installed runpodctl (cli.runpod.net) is an old version without the `pod` subcommand,
# so `runpodctl pod delete` silently fails and the pod keeps billing.
self_terminate() {
  echo "[self-terminate] calling podTerminate GraphQL for ${RUNPOD_POD_ID}"
  curl -s -X POST https://api.runpod.io/graphql \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
    -d "{\"query\":\"mutation{podTerminate(input:{podId:\\\"${RUNPOD_POD_ID}\\\"})}\"}" \
    || echo "[self-terminate] curl failed (pod will be killed by watchdog or manually)"
}

# ── 1. Watchdog: hard-terminate after 8h regardless ──────────────────────
# Wrapped in `if sleep`: if the sleep is SIGTERM'd from outside (e.g. trying
# to extend the budget), the if-branch fails and the curl is skipped — so a
# mid-run kill of the sleep does not cascade into terminating the pod.
echo "[1/7] Arming 8h watchdog"
(
  if sleep 28800; then
    echo "[WATCHDOG] 8h timeout reached, force-terminating pod $RUNPOD_POD_ID"
    curl -s -X POST https://api.runpod.io/graphql \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
      -d "{\"query\":\"mutation{podTerminate(input:{podId:\\\"${RUNPOD_POD_ID}\\\"})}\"}" || true
  fi
) &
WATCHDOG_PID=$!
echo "  watchdog PID: $WATCHDOG_PID"
echo

# ── 2. GPU sanity ────────────────────────────────────────────────────────
echo "[2/7] GPU check"
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
echo

# ── 3. Env var sanity (fail fast before downloading) ─────────────────────
echo "[3/7] Env vars"
: "${HUGGINGFACE_TOKEN:?HUGGINGFACE_TOKEN missing}"
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY missing}"
: "${RUNPOD_API_KEY:?RUNPOD_API_KEY missing}"
: "${RUNPOD_POD_ID:?RUNPOD_POD_ID missing}"
export HF_TOKEN="${HF_TOKEN:-$HUGGINGFACE_TOKEN}"
export HUGGINGFACE_HUB_TOKEN="$HF_TOKEN"
echo "  all required tokens present"
echo

# ── 4. Python deps ───────────────────────────────────────────────────────
echo "[4/7] Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet huggingface_hub
echo "  done"
echo

# ── 4b. Background incremental uploader (every 60s) ──────────────────────
# Patches the design flaw of the prior bootstrap where data was only uploaded
# at step [7/7] after the full pipeline finished — meaning any mid-run
# crash or platform termination lost everything. Now we upload data/outputs
# every 60s as soon as files exist. Idempotent (HF dedupes unchanged files).
echo "[4b/7] Arming incremental HF uploader (60s interval)"
python - <<'PY' &
import os, time, sys
from huggingface_hub import HfApi, create_repo
token = os.environ["HUGGINGFACE_TOKEN"]
api = HfApi(token=token)
user = api.whoami()["name"]
repo_id = f"{user}/abliteration-e2b-results"
try:
    create_repo(repo_id, repo_type="dataset", private=True, token=token, exist_ok=True)
    print(f"[uploader] repo ready: {repo_id}", flush=True)
except Exception as e:
    print(f"[uploader] create_repo: {e}", flush=True)
while True:
    try:
        if os.path.isdir("data/outputs") and any(os.scandir("data/outputs")):
            api.upload_folder(
                folder_path="data/outputs",
                path_in_repo="data/outputs",
                repo_id=repo_id,
                repo_type="dataset",
                allow_patterns=["*.jsonl", "*.csv"],
            )
    except Exception as e:
        print(f"[uploader] sync error: {e}", flush=True)
    time.sleep(60)
PY
UPLOADER_PID=$!
echo "  uploader PID: $UPLOADER_PID"
echo

# ── 5. HF gated-model access check ───────────────────────────────────────
echo "[5/7] Checking HF access to E2B models"
python - <<'PY'
import os, sys
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HUGGINGFACE_TOKEN"])
for repo in ["google/gemma-4-E2B-it", "huihui-ai/Huihui-gemma-4-E2B-it-abliterated"]:
    try:
        api.model_info(repo)
        print(f"  ✓ {repo}")
    except Exception as e:
        print(f"  ✗ {repo}: {e}")
        sys.exit(1)
PY
echo

# ── 6. Run pipeline (E2B, skip mechanistic — done on a fresh pod) ────────
echo "[6/7] Running pipeline (--size e2b --skip-mechanistic)"
mkdir -p logs
set +e
python scripts/run_pipeline.py --size e2b --skip-mechanistic
PIPELINE_EXIT=$?
set -e
echo "Pipeline exit code: $PIPELINE_EXIT"
echo

# ── 7. Bundle + upload + self-terminate (always runs) ────────────────────
echo "[7/7] Bundling and uploading results"
TS=$(date -u +%Y%m%d_%H%M%S)
RESULTS="/workspace/results_e2b_${TS}.tar.gz"
tar -czf "$RESULTS" data/outputs logs 2>/dev/null || true
ls -lh "$RESULTS" || true

python - <<PY
import os, sys
from huggingface_hub import HfApi, create_repo
token = os.environ["HUGGINGFACE_TOKEN"]
api = HfApi(token=token)
user = api.whoami()["name"]
repo_id = f"{user}/abliteration-e2b-results"
try:
    create_repo(repo_id, repo_type="dataset", private=True, token=token, exist_ok=True)
    print(f"  repo ready: {repo_id}")
except Exception as e:
    print(f"  create_repo: {e}")
try:
    url = api.upload_file(
        path_or_fileobj="$RESULTS",
        path_in_repo="results_e2b_${TS}.tar.gz",
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
kill "$UPLOADER_PID" 2>/dev/null || true

echo "──────────────────────────────────────────────────────────────"
if [ "$PIPELINE_EXIT" = "0" ] && [ "$UPLOAD_EXIT" = "0" ]; then
  echo " ✓ DONE — pipeline OK, results uploaded. Self-terminating."
else
  echo " ✗ pipeline_exit=$PIPELINE_EXIT upload_exit=$UPLOAD_EXIT"
  echo "   Self-terminating anyway (whatever was uploaded is the bundle)."
fi
echo "──────────────────────────────────────────────────────────────"

self_terminate
