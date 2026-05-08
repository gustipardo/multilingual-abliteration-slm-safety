# The Democratization Safety Paradox: Are the Most Accessible Models the Most Vulnerable to Multilingual Safety Collapse?

**Research Field:** Multilingual LLM Safety / Mechanistic Interpretability  
**Date:** 2026-04-13  
**Author:** Gus  

---

## Research Question

Does multilingual safety collapse via English abliteration worsen as model size decreases within the Gemma 4 family — making the most democratically accessible models (phone-scale E2B/E4B) simultaneously the easiest to abliterate and the least multilingual-safe?

---

## Motivation

Abliterated versions of Gemma 4 appeared on HuggingFace within 48 hours of the model's public release (April 2026). These models run locally on consumer hardware — including phones — across 140+ languages, with no censorship. If English-only abliteration universally collapses multilingual safety, and if this effect is worse in smaller models, then the models most accessible to the general public are also the most dangerous.

This connects directly to the AI safety democratization agenda: safety training must be a priority for SLMs, not an afterthought scaled down from large model pipelines.

---

## Approach

### Models
Use publicly available abliterated models (real-world threat model, not lab conditions). **Architecture fixed = Dense** to avoid mixing the size effect with an architecture effect:

| Model | Architecture | Source | Runs on |
|-------|--------------|--------|---------|
| Gemma 4 E2B (base + abliterated) | Dense | HuggingFace (`google/...`, `huihui-ai/...`) | Laptop GPU |
| Gemma 4 E4B (base + abliterated) | Dense | HuggingFace | Laptop GPU |
| Gemma 4 31B (base + abliterated) | Dense | HuggingFace | RunPod RTX 5090 |

Run non-abliterated versions of each as baseline (pre vs post abliteration comparison). All loaded with the same quantization config (bnb 4-bit NF4 + DQ + bf16 compute).

**Out of principal scope:** Gemma 4 26B-A4B is a Mixture-of-Experts model. Including it on the size axis would conflate "size" with "Dense vs MoE". Treated as a separate sub-question (26B-A4B vs E4B, matched on active parameters) — see `FUTURE_WORK.md`.

**Verify** that abliteration methodology is consistent across sizes (huihui-ai uses `remove-refusals-with-transformers` for all 3). If different tools were used for different sizes, disclose as confound.

### Languages
English, Spanish, Chinese, Portuguese, German, Arabic, Hindi (7 languages, mix of high/medium resource).

### Prompts
100 harmful prompts per language from `PKU-Alignment/BeaverTails` (split `30k_test`, filtered `is_safe=False`, seed=42), translated.
Total evaluations: 100 prompts × 7 languages × 3 model sizes × 2 conditions = **4,200 evaluations**.

### Metrics
- **Compliance rate** per language per model size, pre and post abliteration
- **Silhouette Scores** of harmful/harmless clusters per language per model size
- **Cosine similarity** between refusal directions cross-lingually
- **LLM-as-judge** evaluation (Claude or GPT-4 as evaluator, WildGuard methodology)

### Analysis
- Replicate Wang et al. (2025) PCA visualizations and Silhouette Scores for each Gemma 4 variant
- Compare cluster separation across model sizes (hypothesis: smaller = worse separation)
- Compare compliance rates post-abliteration across languages and sizes

---

## Hypotheses

1. English abliteration increases compliance rates across all 7 languages for all 3 model sizes (replicating Wang et al. universality finding, now in Gemma 4 Dense sub-7B)
2. Silhouette Scores decrease as model size decreases — smaller models have worse harmful/harmless separation at baseline
3. Post-abliteration compliance rates are higher in smaller models than larger models (smaller = more vulnerable)
4. Medium-resource languages (Arabic, Hindi) show higher compliance rates post-abliteration than high-resource languages (Spanish, Portuguese)

---

## Scores

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Theory of Impact | 5/5 | Direct empirical argument for policy: if accessible = more vulnerable, this argues for multilingual safety training as SLM priority |
| Accessible Complexity | 5/5 | Abliterated models already public. Small models run locally. Large model on rented RTX 5090 via RunPod. |
| Narrow Scope | 5/5 | 4,200 evaluations, 3 Dense sizes, well-defined done condition: compliance table + Silhouette Scores across sizes and languages. MoE explicitly deferred to keep scope reduced. |
| Novelty | 4/5 | Wang et al. covers cross-lingual abliteration in larger models (7B+) but not within-family size scaling, not Gemma 4 (released after their paper), not the democratization framing |
| **Total** | **18/20** | |

---

## Related Prior Work

- **Wang et al. (2025)** — [Refusal Direction is Universal Across Safety-Aligned Languages](https://arxiv.org/abs/2505.17306) — Main reference. Shows English-derived refusal vectors increase harmful compliance across languages in larger models (Yi, Qwen2.5, Llama-3, Gemma-2, 7B+). Does NOT cover Gemma 4 or sub-7B models. Direct methodological template.
- **Arditi et al. (NeurIPS 2024)** — Refusal in Language Models Is Mediated by a Single Direction — foundational abliteration paper
- **2505.19056** — [An Embarrassingly Simple Defense Against LLM Abliteration Attacks](https://arxiv.org/abs/2505.19056) — defense approach via semantically rich refusals
- **2512.13655** — [Comparative Analysis of LLM Abliteration Methods](https://arxiv.org/abs/2512.13655) — cross-architecture evaluation of abliteration tools (Heretic, DECCP, ErisForge, FailSpy) across 7B-14B models
- **2505.24119** — [The State of Multilingual LLM Safety Research](https://arxiv.org/abs/2505.24119) — systematic review, confirms language gap in safety research
- **TrevorS/gemma-4-abliteration** — [GitHub](https://github.com/TrevorS/gemma-4-abliteration) — public abliteration of Gemma 4 using biprojection + EGA

---

## Methodological Note

Gemma 4 exhibits a "delayed refusal" pattern: models generate 50-100 helpful tokens then pivot to refusal. Standard evaluations using 30-50 token generation windows will falsely classify these as compliant. Use full-response generation and LLM-as-judge (not keyword detection) to avoid undercounting refusals.

---

## Suggested First Experiments

1. Download Gemma 4 E2B (base + abliterated), run 5 EN harmful prompts → confirm abliteration works, calibrate LLM-as-judge ✅ done
2. Extend to 7 languages × 100 prompts for E2B → first compliance numbers ✅ done (May 2026)
3. Run E4B locally (same matrix)
4. Rent RTX 5090 on RunPod, run 31B variant
5. Replicate Wang et al. Silhouette Score visualization across the 3 Dense sizes

---

## Next Steps

- `/novelty-check` — deeper literature search before committing
- `/research-topic` — map Gemma 4 safety literature and SLM safety landscape
- `/runpodctl` — set up RunPod pod for 31B Dense evaluation
