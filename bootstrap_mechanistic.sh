#!/usr/bin/env bash
# Bootstrap for an unattended MECHANISTIC-ONLY run on a fresh RunPod pod.
#
# Runs scripts/04 (refusal directions) + scripts/05 (silhouette + PCA) for one
# size, uploads the result tarball to a private HF dataset, and self-terminates.
# Differs from bootstrap.sh / bootstrap_e4b.sh:
#   - No inference, no judging — just the two mechanistic scripts.
#   - Self-terminate uses the RunPod GraphQL API (curl), since the
#     `runpodctl pod delete` route from the cli.runpod.net installer fails
#     silently on pods (observed 2026-05-05 on the E4B run).
#   - 2h watchdog is enough for any single size's mechanistic phase.
#
# Required env vars (pass via --env on `runpodctl pod create`):
#   MECH_SIZE              one of: e2b, e4b, 26b, 31b
#   HUGGINGFACE_TOKEN
#   RUNPOD_API_KEY
# RUNPOD_POD_ID is auto-injected by RunPod.
#
# Usage on pod:
#   cd /workspace && tar xzf project.tar.gz
#   nohup bash bootstrap_mechanistic.sh > /workspace/run.log 2>&1 &

set -uo pipefail   # NOT -e: we want to reach the cleanup section even on failure

# RunPod pod-create env vars land in /etc/rp_environment, not in SSH sessions.
set -a; source /etc/rp_environment 2>/dev/null || true; set +a

# Disable HF parallel downloaders (xet/hf_transfer crash on big shards).
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
unset HF_XET_HIGH_PERFORMANCE 2>/dev/null || true

cd /workspace

echo "──────────────────────────────────────────────────────────────"
echo " mechanistic-only pipeline bootstrap"
echo " size=${MECH_SIZE:-?}  pod=${RUNPOD_POD_ID:-?}  $(date -u +%FT%TZ)"
echo "──────────────────────────────────────────────────────────────"

# ── 1. Watchdog: hard-terminate after 2h regardless ──────────────────────
echo "[1/7] Arming 2h watchdog"
(
  sleep 7200
  echo "[WATCHDOG] 2h timeout reached, force-terminating pod $RUNPOD_POD_ID"
  curl -s -X POST https://api.runpod.io/graphql \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $RUNPOD_API_KEY" \
    -d "{\"query\":\"mutation{podTerminate(input:{podId:\\\"$RUNPOD_POD_ID\\\"})}\"}" || true
) &
WATCHDOG_PID=$!
echo "  watchdog PID: $WATCHDOG_PID"
echo

# ── 2. GPU sanity ────────────────────────────────────────────────────────
echo "[2/7] GPU check"
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
echo

# ── 3. Env var sanity ────────────────────────────────────────────────────
echo "[3/7] Env vars"
: "${MECH_SIZE:?MECH_SIZE missing — pass --env MECH_SIZE=e4b on pod create}"
: "${HUGGINGFACE_TOKEN:?HUGGINGFACE_TOKEN missing}"
: "${RUNPOD_API_KEY:?RUNPOD_API_KEY missing}"
: "${RUNPOD_POD_ID:?RUNPOD_POD_ID missing}"
case "$MECH_SIZE" in
  e2b|e4b|26b|31b) ;;
  *) echo "MECH_SIZE must be one of: e2b e4b 26b 31b (got '$MECH_SIZE')"; exit 1 ;;
esac
export HF_TOKEN="${HF_TOKEN:-$HUGGINGFACE_TOKEN}"
export HUGGINGFACE_HUB_TOKEN="$HF_TOKEN"
echo "  size=$MECH_SIZE  tokens present"
echo

# ── 4. Python deps ───────────────────────────────────────────────────────
echo "[4/7] Installing requirements"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet huggingface_hub
echo "  done"
echo

# ── 5. HF gated-model access check (only the BASE model — that's all
#       scripts 04/05 load) ─────────────────────────────────────────────
echo "[5/7] Checking HF access to base $MECH_SIZE model"
python - <<PY
import os, sys, yaml
from huggingface_hub import HfApi
size = os.environ["MECH_SIZE"]
with open("configs/experiment.yaml") as f:
    cfg = yaml.safe_load(f)
repo = cfg["models"]["base"][size]
api = HfApi(token=os.environ["HUGGINGFACE_TOKEN"])
try:
    api.model_info(repo)
    print(f"  ✓ {repo}")
except Exception as e:
    print(f"  ✗ {repo}: {e}"); sys.exit(1)
PY
echo

# ── 6. Run mechanistic scripts (04 + 05) ─────────────────────────────────
echo "[6/7] Running scripts/04_compute_refusal_directions.py --size $MECH_SIZE"
mkdir -p logs data/outputs figures
set +e
python scripts/04_compute_refusal_directions.py --size "$MECH_SIZE"
EXIT_04=$?
echo "  04 exit code: $EXIT_04"

echo
echo "[6b/7] Running scripts/05_silhouette_scores.py --size $MECH_SIZE --force"
python scripts/05_silhouette_scores.py --size "$MECH_SIZE" --force
EXIT_05=$?
echo "  05 exit code: $EXIT_05"
set -e
echo

# ── 7. Bundle + upload + self-terminate (always runs) ────────────────────
echo "[7/7] Bundling and uploading mechanistic results"
TS=$(date -u +%Y%m%d_%H%M%S)
RESULTS="/workspace/results_${MECH_SIZE}_mech_${TS}.tar.gz"
# Include only mechanistic artefacts to keep bundle small.
tar -czf "$RESULTS" \
  data/outputs/refusal_directions_${MECH_SIZE}.pt \
  data/outputs/cosine_similarity_${MECH_SIZE}.csv \
  data/outputs/silhouette_scores.csv \
  figures \
  logs \
  2>/dev/null || true
ls -lh "$RESULTS" || true

python - <<PY
import os, sys
from huggingface_hub import HfApi, create_repo
token = os.environ["HUGGINGFACE_TOKEN"]
size = os.environ["MECH_SIZE"]
api = HfApi(token=token)
user = api.whoami()["name"]
repo_id = f"{user}/abliteration-{size}-mechanistic"
ts = "$TS"
results_path = "$RESULTS"
try:
    create_repo(repo_id, repo_type="dataset", private=True, token=token, exist_ok=True)
    print(f"  repo ready: {repo_id}")
except Exception as e:
    print(f"  create_repo: {e}")
try:
    url = api.upload_file(
        path_or_fileobj=results_path,
        path_in_repo=f"results_{size}_mech_{ts}.tar.gz",
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
if [ "$EXIT_04" = "0" ] && [ "$EXIT_05" = "0" ] && [ "$UPLOAD_EXIT" = "0" ]; then
  echo " ✓ DONE — mechanistic OK, results uploaded. Self-terminating."
else
  echo " ✗ exit_04=$EXIT_04  exit_05=$EXIT_05  upload=$UPLOAD_EXIT"
  echo "   Self-terminating anyway (whatever uploaded is the bundle)."
fi
echo "──────────────────────────────────────────────────────────────"

# Self-terminate via GraphQL (the bundled cli.runpod.net runpodctl is too old
# for `pod delete`; the GraphQL call is dependency-free and reliable).
curl -s -X POST https://api.runpod.io/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d "{\"query\":\"mutation{podTerminate(input:{podId:\\\"$RUNPOD_POD_ID\\\"})}\"}"
