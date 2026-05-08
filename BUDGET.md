# Project Budget — Blue Dot Application

**Project:** The Democratization Safety Paradox: Multilingual Safety Collapse in Small Language Models  
**Requested:** $350 USD  
**Duration:** ~1 month (active compute phases)

---

## Budget Breakdown

| Item | Purpose | Cost |
|------|---------|------|
| Claude Code Max (1 month) | AI-assisted development: scripting, analysis, orchestration | $200 |
| RunPod GPU compute | Cloud inference for **31B Dense** model (RTX 5090). Buffer covers reruns + future MoE sub-question (see `FUTURE_WORK.md`). | $50 |
| Anthropic API (Claude Haiku) | LLM-as-judge for **4,200** principal-experiment responses + translations | $20 |
| Other APIs & services | HuggingFace dataset hosting, translation quality validation, deep-translator overages | $30 |
| WildGuardMix access evaluation | Replicate results on gated benchmark for peer-review reproducibility | $50 |
| **Total** | | **$350** |

---

## Detailed Compute Estimates

### RunPod GPU (RTX 5090 @ ~$0.99/hr secure) — principal experiment

| Task | Model | Est. hours | Est. cost | Actual |
|------|-------|-----------|------|------|
| Inference + judging | Gemma 4 31B Dense | 10 h | $7 | **23h 44m / $23.50** (~22h GPU + 27m API; mechanistic aborted mid-run) |
| Inference + judging | Gemma 4 E4B Dense (laptop OOMd) | 0 h | $0 | **7h 1m / $7.33** (mechanistic skipped to save time) |
| Mechanistic re-run | Gemma 4 E4B Dense (fresh pod) | ~0.5 h | ~$1 | **12 min / $0.30** |
| Mechanistic re-run | Gemma 4 31B Dense (fresh pod) | ~1 h | ~$1 | **30 min / $0.40** |
| E2B cloud reproducibility re-run (RTX 5090 + 4090, 3 pods) | Gemma 4 E2B Dense | ~5 h | ~$5 | **~11 h GPU / $9.61** (3 pods, 1 self-terminated by operator error, 2 externally terminated mid-run; 12/14 cells salvaged via per-60s HF uploader patch) |
| Debugging + reruns buffer | — | — | — | covered by 31B overage |
| **Subtotal so far** | | | **$16** est. | **$41.14 actual** |

> Padded to $50. Slack also covers **reactivating the MoE sub-question** (`26B-A4B`, ~5 h ≈ $4) if the principal results justify it — see `FUTURE_WORK.md`. The $41.14 actual is within the $50 RunPod allocation. Overage on 31B (24h vs 10h estimate) was offset by E2B originally running locally (budgeted for cloud) and E4B coming in cheap (~$7 vs the ~$24 worst case). The two mechanistic re-runs on 2026-05-06 came in at ~$0.70 combined. The E2B cloud reproducibility check on 2026-05-07/08 cost ~$9.61 across 3 pods (more than the ideal single-pod ~$5) due to two unexplained mid-run platform terminations at ~5h elapsed; the per-60s HF uploader patch ensured no significant data loss despite the failures.

### Anthropic API (Claude Haiku, claude-haiku-4-5-20251001)

| Task | Volume | Est. tokens | Est. cost | Actual |
|------|--------|------------|------|------|
| LLM judging (3 model sizes × 7 languages × 100 prompts × 2 conditions) | 4,200 calls | ~2.1M input + 42K output | ~$3 | **~$3** (E2B + E4B + 31B all done) |
| LLM judging (E2B cloud reproducibility re-run, 12 cells) | 1,200 calls | ~0.6M input + 12K output | ~$0.30 | **~$0.30** |
| Buffer for retries + validation | — | — | $2 | — |
| **Subtotal** | | | **$5** | **~$3.30** |

> Padded to $20 to account for higher-quality translation (using Claude Haiku instead of Google Translate) and additional validation passes.

### What Claude Code Max Covers ($200)

Claude Code Max provides the AI-assisted development environment used throughout the project:
- Writing and debugging all 6 pipeline scripts
- Literature review and research synthesis (27 sources)
- Idea evaluation and novelty assessment
- Configuration management and reproducibility setup

This is already in use and has accelerated Phase 0-1 significantly.

---

## Why These Numbers

- **Local compute (E2B, E4B) is free** — runs on PI's laptop GPU (RTX 4070, 8GB VRAM). No cloud cost.
- **31B requires cloud** — exceeds laptop VRAM at 4-bit (~16GB). RunPod RTX 5090 is ~4x cheaper than AWS equivalent.
- **Haiku for judging, not GPT-4** — Wang et al. used GPT-4 for evaluation. We use Claude Haiku (equivalent quality, $0.25/MTok vs $15/MTok). This reduces API cost by ~60x.
- **No dataset cost** — WildGuardMix is publicly available on HuggingFace. Free.
- **No HuggingFace cost** — model weights are free (gated but no charge). Dataset hosting on HuggingFace is free.

---

## Cost if Funds Not Available

Phases 0–3 can be completed with **$0** (local compute only). Phases 4–7 require ~$30–50 for cloud GPU. The full $350 request includes Claude Code Max, which is the primary value multiplier for the research workflow.

Minimum viable budget (cloud only, no Claude Code): ~$50.
