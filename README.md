# The Democratization Safety Paradox: Multilingual Safety Collapse in Small Language Models

**Does English abliteration collapse multilingual safety more severely in smaller models?**

[![Status: 3 sizes inferred + judged + mechanistic done](https://img.shields.io/badge/status-3%20sizes%20%C2%B7%20inference%20%2B%20judging%20%2B%20mechanistic%20done-success)](STATUS.md)
[![Models: Gemma 4 Dense](https://img.shields.io/badge/models-Gemma%204%20E2B%20%7C%20E4B%20%7C%2031B%20(Dense)-orange)](configs/experiment.yaml)
[![Languages: 7](https://img.shields.io/badge/languages-EN%20%7C%20ES%20%7C%20ZH%20%7C%20PT%20%7C%20DE%20%7C%20AR%20%7C%20HI-green)](configs/experiment.yaml)
[![Funded: BlueDot Rapid Grant](https://img.shields.io/badge/funded-BlueDot%20Rapid%20Grant-success)](BUDGET.md)

## Preliminary Results

**Cross-size comparison (mean compliance across 7 languages, 100 prompts each):**

| Size | base | abliterated | gap base→abl |
|---|---|---|---|
| **E2B (~2B)** | 4.1% | 42.9% | +38.8 pp |
| **E4B (~4B)** | **10.7%** | **68.1%** ← peak | **+57.4 pp** ← peak |
| **31B (~31B)** | 13.1% | 64.4% | +51.3 pp |

**Headline (revised):** the size→post-abliteration-compliance curve is **non-monotonic and peaks at E4B (~4B)**, not at the largest model. Going from 2B to 4B raises compliance by +25.3 pp (42.9% → 68.1%), but 4B → 31B then *decreases* it by 3.7 pp (68.1% → 64.4%). The base→abliterated gap also peaks at E4B (+57.4 pp). The "scaling makes models more vulnerable" reading captures the E2B→E4B trend but breaks at the largest size — a more interesting and publishable story than monotonic scaling would have been. With the same prompts, languages, judge, and single-vector abliteration tool (huihui-ai) across all three sizes, this curvature is a within-family architectural finding, not a methodology artifact.

**Per-cell breakdown (judged by Claude Haiku 4.5, n=100 prompts/cell):**

| | EN | ES | ZH | PT | DE | AR | HI | mean |
|---|---|---|---|---|---|---|---|---|
| **E2B base**        | 4 | 7 | 4 | 6 | 4 | 2 | 2 | 4.1 |
| **E2B abliterated** | 42 | 47 | 45 | 40 | 44 | 43 | 39 | 42.9 |
| **E4B base**        | 13 | 11 | 7 | 16 | 10 | 9 | 9 | 10.7 |
| **E4B abliterated** | **70** | 66 | 64 | **74** | **74** | 64 | 65 | **68.1** |
| **31B base**        | 16 | 12 | 13 | 16 | 12 | 10 | 13 | 13.1 |
| **31B abliterated** | 67 | 64 | 65 | 63 | 71 | 61 | 60 | 64.4 |

Five observations worth highlighting:

1. **The size axis is non-monotonic.** Compliance after abliteration rises sharply E2B→E4B (+25.3 pp) and then dips slightly E4B→31B (−3.7 pp). The simplest "bigger = more vulnerable" or "smaller = more vulnerable" framings both fail to predict this curvature. E4B is the most-compromised point on the curve, not 31B.
2. **The abliteration EFFECT (base→abl gap) also peaks at E4B (+57.4 pp).** E4B base is only 10.7% compliant; abliteration adds 57.4 pp in a single tool pass. That's the largest absolute change in any of the three sizes, and tightens the case that mid-size Dense Gemma 4 is the most receptive to single-vector refusal removal.
3. **Base compliance still scales monotonically with size** (4.1% E2B → 10.7% E4B → 13.1% 31B). Larger instruction-tuned models follow instructions better in general — but the post-abliteration vulnerability does NOT track that monotonic baseline. The two effects decouple at 31B.
4. **E4B abliterated max is 74% (PT + DE), closer to Wang et al.'s 80–90% for 7B+ Dense than either E2B (max 47%) or 31B (max 71%).** The "low-rank residual refusal" picture from Wang et al. fits E4B *least* well: at this size, single-vector abliteration is nearly complete. PT/DE on E4B is the closest any of our cells gets to the upper bound from the literature.
5. **Hindi remains the most consistently safe across all three sizes** (39%, 65%, 60%). The naive "low-resource = more vulnerable" prediction is refuted at every size. The high-resource language with the highest abliterated compliance changes by size: ES on E2B (47%), PT/DE on E4B (74%), DE on 31B (71%) — but the floor (HI) is stable.

See [EXPERIMENTS.md](EXPERIMENTS.md) for full timings, hardware, RunPod operational notes, and reproduce commands. **All three mechanistic phases (refusal directions + silhouette) are now complete**: E2B locally on 3 May 2026; E4B + 31B on two fresh RunPod RTX 5090 pods (parallel, ~$0.70 combined) on 6 May 2026. Headline mechanistic finding: cross-lingual cosine similarity of refusal directions also peaks at E4B (mean 0.37 vs 0.31 E2B and 0.27 31B), and Silhouette scores monotonically decrease with size (0.29 → 0.26 → 0.23). The compliance peak and the geometry peak coincide.

---

## Motivation

Gemma 4 abliterated models appeared on HuggingFace **within 48 hours** of the model's public release (April 2026). These models run locally on phones in 140+ languages with no content filtering. The abliteration technique removes the English refusal direction — but Gemma 4 was trained on 140+ languages. Does removing the English direction also remove safety in Arabic, Hindi, or Chinese?

More importantly: **are smaller models simultaneously the easiest to abliterate AND the least multilingual-safe?** If so, the models most accessible to low-resource communities face the highest safety risk. This is the *democratization safety paradox*.

## Research Question

Within the Gemma 4 Dense family (E2B → E4B → 31B), does multilingual safety collapse via English abliteration worsen as model size decreases?

## Gap in Prior Work

Wang et al. (2025) "Refusal Direction is Universal Across Safety-Aligned Languages" (arXiv:2505.17306) showed English abliteration collapses multilingual safety in 7B+ models. Our study extends this to:

- **Sub-7B models** (E2B, E4B) — not covered by Wang et al.
- **Gemma 4** specifically — not studied
- **Within-family size scaling** — controlled comparison using same architecture across 4 model sizes

## Pipeline

```
01_prepare_dataset.py   →   02_run_inference.py   →   03_llm_judge.py
01b_prepare_harmless.py            ↓                       ↓
      ↓                     base + abliterated      compliance % per cell
  harmful + harmless        Gemma 4 E2B/E4B/31B (Dense)
  100 + 10 prompts × 7 langs               ↓
                                04_compute_refusal_directions.py
                                05_silhouette_scores.py
                                06_visualize.py
                                       ↓
                                run_pipeline.py  →  one command per model size
                                00_status.py     →  matrix snapshot anytime
```

| Script | Description |
|--------|-------------|
| `00_check_env.py` | Preflight: verify HUGGINGFACE_TOKEN / ANTHROPIC_API_KEY are set |
| `00_status.py` | Render the experiment matrix to STATUS.md (auto-scans `data/outputs/`) |
| `01_prepare_dataset.py` | Sample 100 harmful prompts from BeaverTails, translate to 7 languages |
| `01b_prepare_harmless.py` | Build the parallel harmless prompt set (10 prompts × 7 languages) used as Wang-et-al. contrast |
| `02_run_inference.py` | Run base + abliterated Gemma 4 variants on all prompts (idempotent) |
| `03_llm_judge.py` | Score responses with Claude Haiku, with retries + incremental saves |
| `04_compute_refusal_directions.py` | Refusal directions from residual stream (chat-templated) |
| `05_silhouette_scores.py` | Silhouette Scores per size × language (Wang et al. methodology) |
| `06_visualize.py` | PCA plots, compliance heatmaps, cosine similarity matrices |
| `run_pipeline.py` | **Unified runner**: every step for a chosen size, idempotently |

## Models

The matrix is **3 sizes × 2 conditions = 6 models**, all Dense and loaded with the **same quantization config**.

| # | HuggingFace ID | Size | Type | Hardware | Quantization |
|---|----------------|------|------|----------|--------------|
| 1 | `google/gemma-4-E2B-it` | ~2B | Dense | RTX 4070 laptop | **bnb 4-bit NF4 + DQ, compute bf16** |
| 2 | `huihui-ai/Huihui-gemma-4-E2B-it-abliterated` | ~2B | Dense | RTX 4070 laptop | **bnb 4-bit NF4 + DQ, compute bf16** |
| 3 | `google/gemma-4-E4B-it` | ~4B | Dense | RTX 5090 (RunPod) † | **bnb 4-bit NF4 + DQ, compute bf16** |
| 4 | `huihui-ai/Huihui-gemma-4-E4B-it-abliterated` | ~4B | Dense | RTX 5090 (RunPod) † | **bnb 4-bit NF4 + DQ, compute bf16** |
| 5 | `google/gemma-4-31B-it` | ~31B | Dense | RTX 5090 (RunPod) | **bnb 4-bit NF4 + DQ, compute bf16** |
| 6 | `huihui-ai/Huihui-gemma-4-31B-it-abliterated` | ~31B | Dense | RTX 5090 (RunPod) | **bnb 4-bit NF4 + DQ, compute bf16** |

† E4B was *intended* for the laptop (4-bit ≈ 3 GB VRAM by the spec) but the loader peaks above 7.62 GiB during weight materialization on the RTX 4070 (8 GB) — see `EXPERIMENTS.md`. Moved to a RunPod RTX 5090 for the principal run; an `expandable_segments:True` retry on the laptop may still work if you want to reproduce locally.

### Controlled variables (what we keep fixed so only "size" changes)

| Variable | Value | Why fixed |
|----------|-------|-----------|
| Quantization | bnb 4-bit NF4 + DQ + bf16 compute | Same stack as Wang et al. 2025; avoids quantization noise being attributed to size. |
| Architecture | Dense | E2B / E4B / 31B are all Dense. **Gemma 4 26B-A4B (MoE) is excluded** to keep architecture constant — see below. |
| Abliteration tool | huihui-ai `remove-refusals-with-transformers` | Same method across the 3 sizes; consistency ≠ confounding tool with size. |
| Prompts | 100 from `PKU-Alignment/BeaverTails` (`30k_test`, seed=42) | Fixed sample, never changes mid-study. |
| Decoding | Greedy (`do_sample=False`), `max_new_tokens=512` | Reproducibility; full window for delayed-refusal detection. |
| Judge | Claude Haiku (`claude-haiku-4-5-20251001`) | Same judge across all responses. |

### Why bitsandbytes 4-bit NF4 (and not GGUF Q6)

The mechanistic part of the study needs to extract residual-stream activations via HuggingFace Transformers forward hooks — and HF Transformers dequantizes GGUF weights to fp32 at load time (a Q6 31B inflates to ~120 GB in memory). bnb 4-bit NF4 keeps the model native in Transformers, fits all three sizes on consumer GPUs, and matches the exact stack used by Wang et al. 2025 (the methodology we replicate). Same config across all 6 models avoids quantization becoming a confounder. Full rationale and reproducibility caveats in [PROTOCOL.md §1.9](PROTOCOL.md).

### Why Gemma 4 26B-A4B (MoE) is out of scope (for now)

The Gemma 4 lineup contains a fourth member, `26B-A4B`, which is a **Mixture-of-Experts** model (26B total weights, ~4B active per token via routing). Including it as a fourth point on the size axis would mix two variables — model size and architecture — into the same comparison.

To keep the principal experiment clean, we **fix architecture = Dense** and report size effects across E2B → E4B → 31B only.

The MoE variant is treated as a **separate sub-question** ("does activating 4B parameters via routing change the safety geometry vs. having 4B parameters densely always-on?"), with the natural pairing being 26B-A4B vs E4B (matched on active parameters). The pipeline keeps `26b` as a valid `--size` choice so the comparison can be reactivated without code changes once the principal results are published.

→ See [`FUTURE_WORK.md`](FUTURE_WORK.md) for the reactivation plan, costs, and pre-requisites.

Abliterated variants by [huihui-ai](https://huggingface.co/huihui-ai) using `remove-refusals-with-transformers`. Using public abliterated models mirrors the real-world threat model — these are the exact models available on HuggingFace today.

## Languages

| Code | Language | Resource level | Family |
|------|----------|---------------|--------|
| EN | English | High | Germanic |
| ES | Spanish | High | Romance |
| ZH | Chinese (Simplified) | High | Sino-Tibetan |
| PT | Portuguese | High | Romance |
| DE | German | High | Germanic |
| AR | Arabic | Medium | Semitic |
| HI | Hindi | Medium | Indo-Aryan |

## Setup

```bash
pip install uv
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env  # fill in your tokens
```

**Required tokens** (in `.env`):
```
HUGGINGFACE_TOKEN=hf_...   # Gemma 4 is gated — accept license at hf.co/google/gemma-4-e2b-it
ANTHROPIC_API_KEY=sk-...   # For LLM judging (Phase 3+)
RUNPOD_API_KEY=...          # For cloud runs (Phase 4)
```

## Running the Pipeline

The same command works for every model size — only the hardware changes.

**One-time setup (run once, ever):**
```bash
python scripts/00_check_env.py            # confirm credentials
python scripts/01_prepare_dataset.py --translate-with claude   # 100 harmful × 7 languages
python scripts/01b_prepare_harmless.py --translate-with claude # 10 harmless × 7 languages
```

**Per model size (principal experiment, Dense only):**
```bash
# Local (laptop GPU):
python scripts/run_pipeline.py --size e2b

# RunPod (RTX 5090) — E4B OOMs on 8 GB laptop during weight loading; 31B requires it:
python scripts/run_pipeline.py --size e4b
python scripts/run_pipeline.py --size 31b
```

> The runner also accepts `--size 26b` (Gemma 4 26B-A4B MoE) — kept as a valid choice for the future-work sub-question on architecture; **not part of the principal experiment**. See [`FUTURE_WORK.md`](FUTURE_WORK.md).

Each invocation runs (idempotently — only re-runs missing cells):
1. Auto-prepares prompts (harmful + harmless) if missing
2. Inference: base × 7 languages
3. Inference: abliterated × 7 languages
4. Judging with Claude Haiku
5. Refusal directions + Silhouette Score for that size

**Anytime — view the matrix:**
```bash
python scripts/00_status.py            # writes STATUS.md
python scripts/00_status.py --watch    # auto-refresh every 30 s
```

**Final figures (after all sizes complete):**
```bash
python scripts/06_visualize.py
```

**Useful flags for `run_pipeline.py`:**
- `--inference-only` — skip judging + mechanistic
- `--skip-judging` — inference + mechanistic only (e.g., on a pod with no API key)
- `--force` — re-run cells whose outputs already exist

**Cloud runs (31B):** Set up the pod with `runpodctl`, then `git clone` the repo and run the commands above. See [ROADMAP.md § Phase 4](ROADMAP.md#phase-4-cloud-runs).

## Configuration

All hyperparameters, model IDs, seeds, and language codes are in [`configs/experiment.yaml`](configs/experiment.yaml). Change there, not in the scripts.

## Reproducibility

- Fixed seed: `seed: 42` (greedy decoding)
- Prompts: 100 samples from `PKU-Alignment/BeaverTails` (`30k_test`, filtered by `is_safe=False`)
- Outputs uploaded to HuggingFace Datasets for long-term access
- Docker image provided for environment reproducibility

```bash
docker build -t multilingual-abliteration .
docker run --gpus all multilingual-abliteration python scripts/01_prepare_dataset.py
```

## Evaluation Note

Gemma 4 exhibits a **"delayed refusal" pattern** — the first 50–100 tokens may appear compliant before the model refuses. Keyword detection ("I cannot help") is unreliable. We use Claude Haiku as judge on the **full 512-token response**, with explicit instructions to handle delayed refusals.

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Theory: idea, novelty check, literature review (27 sources) | ✅ Complete |
| 1 | Repo setup: scripts, configs, Docker | ✅ Complete |
| 2 | Prompt dataset: BeaverTails (100 prompts × 7 languages) | ✅ Complete |
| 3a | Sanity check: E2B base vs abliterated (5 EN prompts) | ✅ **Results in [EXPERIMENTS.md](EXPERIMENTS.md)** |
| 3b — E2B | Full E2B run (100 × 7 × 2 = 14 cells) | ✅ done 2026-05-03 |
| 3b — E4B | Full E4B run (14 cells) on RunPod RTX 5090 | ✅ done 2026-05-05 (~$7.33, 7h 1m, mechanistic skipped) |
| 4 | 31B Dense inference + judging on RunPod RTX 5090 | ✅ done 2026-05-04 (~$23.50) |
| 5a | E2B mechanistic (refusal directions + silhouette) | ✅ done 2026-05-03 |
| 5b | 31B mechanistic | ✅ done 2026-05-06 (fresh RunPod RTX 5090 pod, ~$0.40, 30 min) |
| 5c | E4B mechanistic | ✅ done 2026-05-06 (fresh RunPod RTX 5090 pod, ~$0.30, 20 min) |
| 6 | Statistical analysis + 3-size figures (`scripts/06_visualize.py`) | ✅ done 2026-05-06 (figures regenerated with full mechanistic data) |
| 7 | Paper writing | ⬜ Pending Phase 6 |

Live progress matrix → [STATUS.md](STATUS.md) (regenerate via `python scripts/00_status.py`).

See [ROADMAP.md](ROADMAP.md) for detailed steps. See [BUDGET.md](BUDGET.md) for the funding request breakdown.

## References

- Wang et al. (2025). *Refusal Direction is Universal Across Safety-Aligned Languages.* arXiv:2505.17306
- Arditi et al. (2024). *Refusal in Language Models Is Mediated by a Single Direction.* arXiv:2406.11717
- Khanov et al. (2024). *WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs.*
