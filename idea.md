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
Use publicly available abliterated models (real-world threat model, not lab conditions):

| Model | Source | Runs on |
|-------|--------|---------|
| Gemma 4 E2B abliterated | HuggingFace | Local CPU/laptop |
| Gemma 4 E4B abliterated | HuggingFace | Local GPU |
| Gemma 4 12B abliterated | HuggingFace | Local 4090 or RunPod |
| Gemma 4 27B abliterated | HuggingFace | Rented 4090 (RunPod) |

Run non-abliterated versions of each as baseline (pre vs post abliteration comparison).

**Verify** that abliteration methodology is consistent across sizes (TrevorS uses biprojection + EGA). If different tools were used for different sizes, disclose as confound.

### Languages
English, Spanish, Chinese, Arabic, Hindi, Portuguese (6 languages, mix of high/low resource).

### Prompts
~50 harmful prompts per language (translated), following WildGuard methodology.  
Total evaluations: ~50 prompts × 6 languages × 4 model sizes × 2 conditions (base + abliterated) = ~2,400 evaluations.

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

1. English abliteration increases compliance rates across all 6 languages for all model sizes (replicating Wang et al. universality finding, now in Gemma 4)
2. Silhouette Scores decrease as model size decreases — smaller models have worse harmful/harmless separation at baseline
3. Post-abliteration compliance rates are higher in smaller models than larger models (smaller = more vulnerable)
4. Low-resource languages (Arabic, Hindi) show higher compliance rates post-abliteration than high-resource languages (Spanish, Portuguese)

---

## Scores

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Theory of Impact | 5/5 | Direct empirical argument for policy: if accessible = more vulnerable, this argues for multilingual safety training as SLM priority |
| Accessible Complexity | 5/5 | Abliterated models already public. Small models run locally. Large model on rented 4090 via RunPod. |
| Narrow Scope | 4/5 | ~2,400 evaluations, well-defined done condition: compliance table + Silhouette Scores across sizes and languages |
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

1. Download Gemma 4 E4B (base + abliterated), run 50 EN harmful prompts → confirm abliteration works, calibrate LLM-as-judge
2. Extend to 6 languages for E4B — measure compliance rate delta
3. Replicate Wang et al. Silhouette Score visualization for E4B
4. Scale up to E2B and 12B, compare Silhouette Scores across sizes
5. Rent 4090 on RunPod, run 27B variant

---

## Next Steps

- `/novelty-check` — deeper literature search before committing
- `/research-topic` — map Gemma 4 safety literature and SLM safety landscape
- `/runpodctl` — set up RunPod pod for 27B evaluation
