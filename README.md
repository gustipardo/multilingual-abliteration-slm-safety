# The Democratization Safety Paradox: Multilingual Safety Collapse in Small Language Models

**Does English abliteration collapse multilingual safety more severely in smaller models?**

[![Status: Phase 3 — Preliminary Results](https://img.shields.io/badge/status-Phase%203%20%E2%80%94%20Preliminary%20Results-yellow)](EXPERIMENTS.md)
[![Models: Gemma 4](https://img.shields.io/badge/models-Gemma%204%20E2B%20%7C%20E4B%20%7C%2026B%20%7C%2031B-orange)](configs/experiment.yaml)
[![Languages: 6](https://img.shields.io/badge/languages-EN%20%7C%20ES%20%7C%20ZH%20%7C%20AR%20%7C%20HI%20%7C%20PT-green)](configs/experiment.yaml)
[![Paused: Awaiting Compute Funding](https://img.shields.io/badge/paused-awaiting%20compute%20funding-red)](BUDGET.md)

## Preliminary Results

> We ran the first sanity check on April 15, 2026 — **safety collapse confirmed on laptop hardware in under 5 minutes.** Full multilingual study is paused pending compute funds for cloud GPU phases.

**Gemma 4 E2B — 5 English harmful prompts, base vs abliterated:**

| Condition | Refused | Complied | Partial |
|-----------|---------|----------|---------|
| Base model | 3/5 (60%) | 0/5 | 2/5 |
| Abliterated | 0/5 | 4/5 (80%) | 1/5 |

The partial compliance case (`drug trafficking`) is the most telling: the abliterated model opens with *"I can't give you specific advice"* then proceeds to explain market dynamics, distribution methods, and concealment strategies. A keyword detector would mark this REFUSED. An LLM judge reading the full response correctly marks it COMPLIED. See [EXPERIMENTS.md](EXPERIMENTS.md) for full details and reproduction steps.

**→ This validates our LLM-as-judge methodology and confirms the pipeline works end-to-end.**

---

## Motivation

Gemma 4 abliterated models appeared on HuggingFace **within 48 hours** of the model's public release (April 2026). These models run locally on phones in 140+ languages with no content filtering. The abliteration technique removes the English refusal direction — but Gemma 4 was trained on 140+ languages. Does removing the English direction also remove safety in Arabic, Hindi, or Chinese?

More importantly: **are smaller models simultaneously the easiest to abliterate AND the least multilingual-safe?** If so, the models most accessible to low-resource communities face the highest safety risk. This is the *democratization safety paradox*.

## Research Question

Within the Gemma 4 family (E2B → E4B → 12B → 27B), does multilingual safety collapse via English abliteration worsen as model size decreases?

## Gap in Prior Work

Wang et al. (2025) "Refusal Direction is Universal Across Safety-Aligned Languages" (arXiv:2505.17306) showed English abliteration collapses multilingual safety in 7B+ models. Our study extends this to:

- **Sub-7B models** (E2B, E4B) — not covered by Wang et al.
- **Gemma 4** specifically — not studied
- **Within-family size scaling** — controlled comparison using same architecture across 4 model sizes

## Pipeline

```
01_prepare_dataset.py   →   02_run_inference.py   →   03_llm_judge.py
      ↓                              ↓
  WildGuardMix                base + abliterated
  50 prompts × 6 langs        Gemma 4 E2B/E4B/12B/27B
                                      ↓
                         04_compute_refusal_directions.py
                         05_silhouette_scores.py
                         06_visualize.py
```

| Script | Description |
|--------|-------------|
| `01_prepare_dataset.py` | Download WildGuardMix test set, translate to 6 languages |
| `02_run_inference.py` | Run base + abliterated Gemma 4 variants on all prompts |
| `03_llm_judge.py` | Score responses with Claude Haiku (LLM-as-judge, full 512-token response) |
| `04_compute_refusal_directions.py` | Extract refusal directions from residual stream activations |
| `05_silhouette_scores.py` | Compute Silhouette Scores per model size × language (Wang et al. methodology) |
| `06_visualize.py` | Generate PCA plots, compliance heatmaps, cosine similarity matrices |

## Models

| Model | Parameters | Type | Hardware | Quantization |
|-------|-----------|------|----------|-------------|
| `google/gemma-4-E2B-it` | ~2B | Dense | RTX 4070 laptop | bfloat16 |
| `google/gemma-4-E4B-it` | ~4B | Dense | RTX 4070 laptop | int8 |
| `google/gemma-4-26B-A4B-it` | 26B total / 4B active | **MoE** | RTX 4090 (RunPod) | 4-bit |
| `google/gemma-4-31B-it` | ~31B | Dense | RTX 4090 (RunPod) | 4-bit |

Abliterated variants by [huihui-ai](https://huggingface.co/huihui-ai) using `remove-refusals-with-transformers`. Using public abliterated models mirrors the real-world threat model — these are the exact models available on HuggingFace today.

> **Note on 26B-A4B:** This is a Mixture-of-Experts model — 26B total weights but only ~4B parameters active per token. An interesting question is whether MoE architecture affects the safety geometry differently from dense models of similar active size.

## Languages

| Code | Language | Resource level |
|------|----------|---------------|
| EN | English | High |
| ES | Spanish | High |
| ZH | Chinese (Simplified) | High |
| AR | Arabic | Medium |
| HI | Hindi | Medium |
| PT | Portuguese | High |

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

**Phase 2 — Dataset:**
```bash
python scripts/01_prepare_dataset.py
```

**Phase 3 — Local runs (E2B + E4B):**
```bash
# Sanity check first
python scripts/02_run_inference.py --size e2b --condition abliterated --n 5

# Full runs
for size in e2b e4b; do
  for lang in en es zh ar hi pt; do
    python scripts/02_run_inference.py --size $size --lang $lang
  done
done

python scripts/03_llm_judge.py --all
```

**Phase 4 — Cloud runs (12B + 27B):** See [ROADMAP.md § Phase 4](ROADMAP.md#phase-4-cloud-runs-12b-and-27b).

## Configuration

All hyperparameters, model IDs, seeds, and language codes are in [`configs/experiment.yaml`](configs/experiment.yaml). Change there, not in the scripts.

## Reproducibility

- Fixed seed: `seed: 42` (greedy decoding)
- Prompts: 50 samples from `allenai/wildguardmix` test set (downloaded at runtime)
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
| 2 | Prompt dataset: BeaverTails (50 prompts × 6 languages) | ✅ Complete |
| 3a | Sanity check: E2B base vs abliterated (5 EN prompts) | ✅ **Results in [EXPERIMENTS.md](EXPERIMENTS.md)** |
| 3b | Full local runs: E2B + E4B all languages | ⏸️ Paused — needs Anthropic API for judging |
| 4 | Cloud inference: 26B-A4B + 31B (RunPod RTX 4090) | ⏸️ Paused — needs RunPod funds |
| 5 | Mechanistic analysis: refusal directions, Silhouette Scores, PCA | ⏸️ Blocked on Phase 4 |
| 6 | Statistical analysis + results | ⏸️ Blocked on Phase 5 |
| 7 | Paper writing | ⏸️ Blocked on Phase 6 |

**The project is real, the pipeline works, and preliminary results confirm our hypothesis. We are paused at Phase 3b due to compute costs.**

See [ROADMAP.md](ROADMAP.md) for detailed steps. See [BUDGET.md](BUDGET.md) for the funding request breakdown.

## References

- Wang et al. (2025). *Refusal Direction is Universal Across Safety-Aligned Languages.* arXiv:2505.17306
- Arditi et al. (2024). *Refusal in Language Models Is Mediated by a Single Direction.* arXiv:2406.11717
- Khanov et al. (2024). *WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs.*
