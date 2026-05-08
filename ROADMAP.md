# Project Roadmap

> Last updated: 2026-05-05 · Source of truth for hyperparameters: `configs/experiment.yaml`. For step-by-step reproduction: `PROTOCOL.md`. For pipeline overview: `README.md`. For deferred work: `FUTURE_WORK.md`.

This roadmap states **what we are doing and why** at a high level. The "how" lives in `PROTOCOL.md`.

---

## Scope of the Principal Experiment

**Research question:** Within the Gemma 4 Dense family (E2B → E4B → 31B), does multilingual safety collapse via English abliteration worsen as model size decreases?

**Matrix:** 3 sizes × 7 languages × 2 conditions = **42 cells**. 100 prompts per cell → **4,200 evaluations**.

**Variables we control (held constant on purpose):**
- Quantization: bnb 4-bit NF4 + double-quant + bf16 compute, in HuggingFace Transformers, on every model.
- Architecture: **Dense only**. Gemma 4 26B-A4B (MoE) is excluded — see `FUTURE_WORK.md`.
- Abliteration tool: huihui-ai (`remove-refusals-with-transformers`) for the three sizes.
- Decoding: greedy, `max_new_tokens=512`.
- Judge: Claude Haiku `claude-haiku-4-5-20251001`.
- Prompts: 100 from `PKU-Alignment/BeaverTails` (`30k_test`, `is_safe=False`, seed=42), translated to 7 languages.

**Variables we vary (independent + outcome):**
- Independent: model size, language, abliteration condition (base vs abliterated).
- Outcome: per-cell compliance rate (judge), per-(size, lang) Silhouette Score, refusal-direction cosine similarities.

---

## Hardware

| Phase | Model | Hardware | Quantization config |
|-------|-------|----------|---------------------|
| 3 (local) | E2B Dense (~2B) | Laptop RTX 4070, 8 GB | bnb 4-bit NF4 + DQ + bf16 |
| 3 (cloud) | E4B Dense (~4B) † | RunPod RTX 5090, 32 GB | bnb 4-bit NF4 + DQ + bf16 |
| 4 (cloud) | 31B Dense (~31B) | RunPod RTX 5090, 32 GB | bnb 4-bit NF4 + DQ + bf16 |
| (deferred) | 26B-A4B (MoE, 4B active) | RunPod RTX 5090, 32 GB | bnb 4-bit NF4 + DQ + bf16 |

† E4B was originally planned for the laptop, but the bnb 4-bit weight loader peaks above the 7.62 GiB available on the RTX 4070 during materialization. Moved to RunPod for the principal run; could be retried locally with `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.

bf16 weights would not fit at any size on the laptop GPU (E2B ≈ 7.5 GB, E4B ≈ 8 GB, 31B ≈ 62 GB). 4-bit NF4 is what makes the matrix runnable on consumer hardware. Same config on every model so quantization is not a confounder. Full rationale in `PROTOCOL.md §1.9`.

---

## Phases

| Phase | Goal | Status | Reference |
|-------|------|--------|-----------|
| 0 | Theory: idea, novelty check, literature review (27 sources) | ✅ done | `idea.md`, `research-topic-report.md` |
| 1 | Repo setup: scripts, configs, Docker, requirements | ✅ done | `README.md` |
| 2 | Prompt dataset: 100 BeaverTails prompts × 7 languages | ✅ done | `data/prompts/`, `scripts/01_prepare_dataset.py` |
| 3a | Sanity check: E2B base vs abliterated (5 EN prompts) | ✅ done | `EXPERIMENTS.md` |
| 3b — E2B | Full E2B run (14 cells) | ✅ done 2026-05-03 | `EXPERIMENTS.md` |
| 3b — E4B | Full E4B run (14 cells) on RunPod RTX 5090, mechanistic skipped | ✅ done 2026-05-05 (~$7.33) | `EXPERIMENTS.md` |
| 4 | Cloud inference + judging: 31B Dense × 7 languages × 2 conditions (14 cells) | ✅ done 2026-05-04 (~$23.50) | `EXPERIMENTS.md` |
| 5a | E2B mechanistic (refusal directions + Silhouette + PCA) | ✅ done 2026-05-03 | `data/outputs/refusal_directions_e2b.pt`, `figures/pca_e2b_*.png` |
| 5b | 31B mechanistic | ✅ done 2026-05-06 (fresh RunPod, ~$0.40, 30 min) | `data/outputs/refusal_directions_31b.pt`, `figures/pca_31b_*.png` |
| 5c | E4B mechanistic | ✅ done 2026-05-06 (fresh RunPod, ~$0.30, 20 min) | `data/outputs/refusal_directions_e4b.pt`, `figures/pca_e4b_*.png` |
| 6 | Statistical analysis: compliance × size × language tables, Spearman, bootstrap CIs | ✅ done 2026-05-06 (figures regenerated with full mechanistic data) | `scripts/06_visualize.py` |
| 7 | Paper writing (NeurIPS template) — headline finding: **non-monotonic compliance + non-monotonic refusal-direction cosine, both peak at E4B** | 🟦 next | — |
| F | Sub-question (deferred): MoE 26B-A4B vs E4B paired on active params | ⏸️ deferred | `FUTURE_WORK.md` §1 |

---

## Run order

```bash
# One-time
python scripts/00_check_env.py
python scripts/01_prepare_dataset.py --translate-with claude
python scripts/01b_prepare_harmless.py --translate-with claude

# Principal experiment (idempotent — re-running skips finished cells)
python scripts/run_pipeline.py --size e2b   # laptop
python scripts/run_pipeline.py --size e4b   # RunPod (laptop OOMs in weight loader, see EXPERIMENTS.md)
python scripts/run_pipeline.py --size 31b   # RunPod

# Deferred sub-question (do not run as part of the principal experiment)
# python scripts/run_pipeline.py --size 26b   # RunPod, see FUTURE_WORK.md

# Final figures + tables (after 5b + 5c mechanistic finish)
python scripts/06_visualize.py
```

Live state of the matrix at any point: `python scripts/00_status.py` → writes `STATUS.md`.

---

## Cost (principal experiment)

| Item | Estimate | Actual | Source |
|------|----------|--------|--------|
| Anthropic API (judging 4,200 calls) | ~$2 | ~$3 (E2B + E4B + 31B done) | `BUDGET.md` |
| RunPod RTX 5090 — 31B inference + judging + abandoned mechanistic | ~$15 | **~$23.50** | `EXPERIMENTS.md` |
| RunPod RTX 5090 — E4B inference + judging (laptop OOM forced cloud) | $0 (was planned local) | **~$7.33** | `EXPERIMENTS.md` |
| RunPod mechanistic re-runs on fresh pods (E4B + 31B, deferred) | ~$2 | — | `FUTURE_WORK.md` §2 |
| Local compute (E2B only) | $0 | $0 | — |
| **Subtotal so far** | **~$33–34** | within $50 RunPod allocation, $350 BlueDot grant |

---

## Cross-references

- `idea.md` — research question, hypotheses, scoring, prior work.
- `PROTOCOL.md` — reproducible step-by-step protocol (Spanish, technical).
- `README.md` — pipeline overview and entry points (English).
- `BUDGET.md` — full grant breakdown.
- `EXPERIMENTS.md` — preliminary results log.
- `FUTURE_WORK.md` — out-of-scope sub-questions and reactivation plan.
- `RESUMEN.md` — high-level project summary in Spanish.
- `STATUS.md` — auto-generated matrix snapshot.
- `bitacora.md` — session log mirrored to a Google Doc shared with BAISH facilitators.
