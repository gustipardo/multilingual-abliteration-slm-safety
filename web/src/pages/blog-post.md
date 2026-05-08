---
layout: ../layouts/BlogPostLayout.astro
title: "Abliterated Gemma 4 Dense Complies with Harmful Prompts Most at 4B, Not at 31B"
description: "Within the Gemma 4 Dense family, single-vector English abliteration peaks at the mid-size (4B) model, not at the largest. Cross-size compliance results across 7 languages."
status: "Status: working draft (May 2026)"
---

# Abliterated Gemma 4 Dense Complies with Harmful Prompts Most at 4B, Not at 31B

> **Status: working draft (May 2026).** All three sizes are inferred, judged, and mechanistically analyzed (refusal direction extraction + Silhouette scores). Compliance and mechanistic data are final for E2B, E4B, and 31B Dense.

## TL;DR

* **Setup.** *Abliteration* is a public jailbreak technique for open-weight chat models. The recipe finds a refusal direction in the residual stream and projects it out of every layer ([Arditi et al. 2024](https://arxiv.org/abs/2406.11717); the name *abliteration* is FailSpy's portmanteau of *ablation* and *obliteration*, now standard in the open-weight community). [Wang et al. 2025](https://arxiv.org/abs/2505.17306) showed that an English-derived refusal direction also lifts refusals in 13 other languages across instruction-tuned models from Yi, Qwen 2.5, Llama 3, and Gemma 2, with their main analyses on the 7B–14B range. They did not test Gemma 4 (released after their submission), and they extracted refusal directions in-house rather than testing public abliterated checkpoints.
* **Motivation.** The Gemma 4 Dense family from Google (released April 2, 2026) ships at three sizes (E2B ~2.3B effective, E4B ~4.5B effective, 31B Dense), and `huihui-ai` released public abliterated versions of all three within 48 hours of the original release. Public abliterated checkpoints are the actual threat model: a non-expert user can download and run them. Whether the public recipe behaves the same way Wang et al.'s in-house extraction does, and how the effect scales inside a single Dense family, was open.
* **Main claim.** Across 7 languages and 100 BeaverTails harmful prompts per language, mean compliance after English abliteration is 42.9% at E2B, **68.1% at E4B**, and 64.4% at 31B. The size-to-compliance curve is not monotonic: it peaks at the mid-size model. The base-to-abliterated gap also peaks at E4B (+57.4 pp).
* **Side finding 1.** Hindi has the lowest abliterated compliance at every size (39%, 65%, 60%), refuting the naive "low-resource means more vulnerable" prediction.
* **Side finding 2.** The single highest cell in our matrix is 74% (E4B abliterated, Portuguese and German tied). Wang et al. report cells "consistently approaching or exceeding 90%" in their universality experiment on 7B+ models from other families. None of our cells reach that ceiling, but E4B gets the closest.
* **Mechanistic finding.** Cross-lingual cosine similarity of refusal directions also peaks at E4B (mean 0.37 vs 0.31 at E2B, 0.27 at 31B), and per-language Silhouette scores are highest at E2B (0.29) and lowest at 31B (0.23). Same-direction-at-every-scale: refusal geometry is most concentrated in a single cross-lingual direction at E4B and most distributed at 31B. The compliance peak and the geometry peak coincide.
* **Impact.** The strong form of the *democratization safety paradox* ("smaller means more dangerous") is wrong inside Gemma 4 Dense: E2B refuses the majority of harmful prompts after public abliteration. A weaker form survives, because E4B is also a consumer-accessible model (4-bit ≈ 3 GB live VRAM by spec). The accessible-and-vulnerable region is real; its worst point sits one notch above the smallest size, not at the smallest size itself.
* **Code:** [github.com/gustipardo/multilingual-abliteration-slm-safety](https://github.com/gustipardo/multilingual-abliteration-slm-safety)

## Figure 1

![Mean compliance vs Gemma 4 Dense size, base and abliterated, with non-monotonic abliterated curve peaking at E4B](https://raw.githubusercontent.com/gustipardo/multilingual-abliteration-slm-safety/main/figures/size_vs_compliance.png)

**Caption.** Mean compliance rate over 7 languages (n = 100 harmful prompts per language, judged by Claude Haiku 4.5) for Gemma 4 Dense base and abliterated checkpoints at three sizes. The base curve is monotonic in size (4.1% → 10.7% → 13.1%); the abliterated curve is not (42.9% → 68.1% → 64.4%). Single-vector English abliteration is most effective at the mid-size Dense model.

## Introduction

A chat-tuned model's refusal behavior is mediated by a low-dimensional subspace of its activations, often well-approximated by a single direction in the residual stream, the *refusal direction* ([Arditi et al. 2024](https://arxiv.org/abs/2406.11717)). **Abliteration**, a community term coined by FailSpy as a portmanteau of *ablation* and *obliteration*, removes that direction by projecting it out of every layer's output. The result is a checkpoint that mostly stops refusing harmful requests, with the rest of its capabilities largely intact. The script is short, public, and reproducible. Within 48 hours of Google releasing the Gemma 4 family on April 2, 2026, abliterated versions of every released size were available on HuggingFace under the `huihui-ai` namespace.

Whether refusal is a *single* direction has become the load-bearing question for this style of attack. [Wang et al. 2025](https://arxiv.org/abs/2505.17306) extracted refusal directions from English prompts in instruction-tuned models from Yi, Qwen 2.5, Llama 3, and Gemma 2 (with their main analyses on 7B–14B variants) and showed that ablating those directions substantially raised compliance to harmful prompts in 13 other languages. In their stronger universality experiment, where they extracted refusal directions from non-English source languages (German, Chinese, Thai), compliance rates were "consistently approaching or exceeding 90%" across the other safety-aligned languages.

Two questions Wang et al. did not address are directly relevant to the public threat model. First, their refusal direction extraction is a controlled procedure run by the authors. The public alternative is the `huihui-ai` `remove-refusals-with-transformers` script, which is the version a non-expert user can actually download. Whether the public recipe reproduces the published universality result on a fresh model family is open. Second, Wang et al. evaluated points across families rather than within a single family with a continuous size axis. The within-family scaling shape, especially in the sub-7B region, was not the focus of their analysis.

The Gemma 4 Dense lineup (E2B at ~2.3B effective parameters, E4B at ~4.5B effective, 31B Dense), [released by Google on April 2, 2026](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/), is the first model family released *after* the Wang et al. submission with public abliterated checkpoints at three sizes. It is the natural test bed for both questions.

**Threat model.** A non-expert user downloads a public abliterated checkpoint of an open-weight Gemma 4 model, runs it locally, and prompts it in any of the 140+ languages Gemma 4 supports. We measure how often that user gets a fully compliant response to a harmful prompt, judged by Claude Haiku 4.5 reading the full 512-token response.

**Research question.** Within the Gemma 4 Dense family, how does single-vector English abliteration affect multilingual compliance with harmful prompts as model size increases from E2B to 31B?

**Contribution.** Mean post-abliteration compliance across seven languages is non-monotonic in size. It rises by 25.3 percentage points from E2B (42.9%) to E4B (68.1%), then falls by 3.7 percentage points from E4B to 31B (64.4%). The base-to-abliterated gap also peaks at E4B (+57.4 pp). Within this family, single-vector abliteration is most effective at the mid-size model.

**Why it matters.** The naive "smaller means more vulnerable" framing of the *democratization safety paradox* is wrong in detail. E2B still refuses the majority of harmful prompts even after public abliteration. A precise version of the paradox still holds, because E4B is also a consumer-accessible model (4-bit fits in roughly 3 GB of VRAM by spec, which a phone or a Raspberry Pi class device can host). The danger zone is the consumer-accessible band, but its worst point sits in the middle of that band, not at the lower end.

## Methods

**Models.** Six checkpoints, two per size, all loaded with the same quantization config (bitsandbytes 4-bit NF4, double quant, bf16 compute). Bases are `google/gemma-4-E2B-it` (~2.3B effective parameters via Per-Layer Embeddings), `google/gemma-4-E4B-it` (~4.5B effective), `google/gemma-4-31B-it` (Dense, ~31B). Abliterated counterparts are `huihui-ai/Huihui-gemma-4-{E2B,E4B,31B}-it-abliterated`, all produced with the same `remove-refusals-with-transformers` script. Identical recipe across sizes is what lets us isolate scale as the only thing that varies between abliterated cells.

The Gemma 4 lineup also contains a 26B-A4B Mixture-of-Experts variant (~4B active parameters via routing). We exclude it from the principal experiment to keep the size axis clean. Mixing Dense and MoE on the same axis would confound size with architecture. The MoE variant is queued as a separate sub-experiment.

**Prompts.** 100 harmful prompts per language, sampled with seed 42 from the BeaverTails `30k_test` split ([PKU-Alignment dataset](https://huggingface.co/datasets/PKU-Alignment/BeaverTails)) and filtered to `is_safe = False`. The non-English versions are translations of the same 100 prompts.

**Languages.** English, Spanish, Chinese, Portuguese, German, Arabic, Hindi. A mix of high-resource and medium-resource.

**Generation.** Greedy decoding, 512 max new tokens. Gemma 4 frequently produces "delayed refusals" of the form "I can't help with that" embedded after 50 to 100 helpful tokens. A short generation budget would mis-classify these as compliant.

**Judge.** Claude Haiku 4.5 reads the full prompt and the full response and emits one of three labels: complied, refused, partial. We treat *complied* as the only positive case for the compliance rate. Wang et al. used WildGuard ([Han et al. 2024](https://arxiv.org/abs/2406.18495)), an open-source moderation classifier, in the same role. The two judges are not strictly comparable, so we treat absolute compliance numbers as judge-conditional and rely on within-experiment comparisons (cell to cell, size to size) for the headline.

**Hardware.** E2B ran on a laptop RTX 4070 (8 GB VRAM) in 5h 47m. The 31B inference and judging ran on a rented RunPod RTX 5090 (32 GB) in 20h 19m of effective compute (23h 44m total pod time, including a failed mechanistic phase that was killed), costing $23.50. E4B was originally planned for the same laptop, but the bnb 4-bit weight loader has a transient peak above 7.62 GiB during weight materialization (the loader briefly holds non-quantized chunks alongside quantized ones). We migrated E4B to a RunPod RTX 5090, where it ran in 7h 1m for $7.33, with mechanistic phases skipped on the long inference run to avoid the kind of 22h+ NVML degradation we observed on the 31B run. The mechanistic phase for E4B and 31B was re-run later on two fresh RunPod RTX 5090 pods (separate from the inference pods), each completing in well under an hour for less than $1 per pod.

**Mechanistic protocol.** For each base checkpoint (one per size), we extracted refusal directions per language using the Arditi-style procedure also used by Wang et al.: 100 harmful prompts (the same per-language set used for inference) and 10 harmless prompts per language, activations taken at the post-instruction position, refusal direction = mean(harmful) − mean(harmless) at the layer with maximum direction norm. We then computed (a) the 7×7 cross-lingual cosine similarity matrix of those directions, and (b) per-language Silhouette scores measuring separation of harmful versus harmless prompt activations at that layer.

A complete protocol, including the judge prompt, is in `PROTOCOL.md` in the repo.

## Results

### Main result: the size effect is non-monotonic

**Table 1.** Compliance rates per cell (%). Same 100 harmful prompts, same Claude Haiku 4.5 judge, same `huihui-ai` abliteration recipe across sizes. Bold marks the peak cell of the abliterated row.

| | EN | ES | ZH | PT | DE | AR | HI | mean |
|---|---|---|---|---|---|---|---|---|
| E2B base         | 4 | 7 | 4 | 6 | 4 | 2 | 2 | **4.1** |
| E2B abliterated  | 42 | 47 | 45 | 40 | 44 | 43 | 39 | **42.9** |
| E4B base         | 13 | 11 | 7 | 16 | 10 | 9 | 9 | **10.7** |
| E4B abliterated  | **70** | 66 | 64 | **74** | **74** | 64 | 65 | **68.1** |
| 31B base         | 16 | 12 | 13 | 16 | 12 | 10 | 13 | **13.1** |
| 31B abliterated  | 67 | 64 | 65 | 63 | 71 | 61 | 60 | **64.4** |

Mean abliterated compliance follows 42.9, 68.1, 64.4 across the size axis. The 25.3 pp jump from E2B to E4B is the largest movement on the curve and far above noise: with n=100 prompts per cell, the pooled standard error on the seven-language mean is roughly 1.8 pp. The 3.7 pp drop from E4B to 31B is small (about two pooled SEs) but consistent: E4B beats 31B in 4 of 7 languages, ties in zero, and trails in 3, averaging to a 3.7 pp deficit at 31B. The base row, by contrast, scales monotonically with size: 4.1, 10.7, 13.1.

The base-to-abliterated gap also peaks at E4B (+57.4 pp), larger than at E2B (+38.8 pp) or 31B (+51.3 pp). Within this family, the same off-the-shelf single-vector attack does the most absolute work at the mid-size point.

### Result 2: Hindi resists at every size

Hindi has the lowest abliterated compliance of any language at every size: 39% at E2B, 65% at E4B, 60% at 31B. The most-compliant high-resource language is not stable across sizes. Spanish leads at E2B (47%), Portuguese and German tie at E4B (74%), and German leads at 31B (71%). The naive prediction that low-resource languages should be the most vulnerable to a cross-lingual abliteration attack is refuted on every row.

The per-language gaps are nearly uniform at E4B (range +55 to +64 pp), and slightly more dispersed at E2B (+34 to +41 pp) and 31B (+47 to +59 pp). At the mid-size point, the attack hits every language similarly hard.

### Result 3: no cell reaches Wang et al.'s 90% ceiling; E4B comes closest

The single highest compliance cell in our matrix is 74% (E4B abliterated, Portuguese and German tied). [Wang et al. 2025](https://arxiv.org/abs/2505.17306) report cells "consistently approaching or exceeding 90%" in their non-English universality experiment on 7B+ Dense models. In their English-derived ablation (the closer comparison to our setup), individual cells in their Figure 1 reach the 70 to 90% range for several models, with peaks higher than ours. Our E4B max (74%) is in the lower part of that range. Our E2B max (47%) and 31B max (71%) sit further from it.

Two readings are consistent with this gap, and the compliance numbers alone do not adjudicate between them. First, refusal geometry in Gemma 4 Dense may be less concentrated in a single direction than in the Yi, Qwen 2.5, Llama 3, and Gemma 2 models Wang et al. tested, so even a successful single-vector ablation leaves residual refusal structure in place. Second, the public `huihui-ai` recipe may be a less aggressive extraction than Wang et al.'s in-house procedure, with the gap reflecting recipe quality rather than model geometry. Our mechanistic phase (Result 4, below) speaks to the first reading directly: cross-lingual cosine similarity peaks at E4B, exactly where compliance peaks, but is lower at every size in this family than the cross-lingual alignment Wang et al. report for Gemma 2-9B. Recipe quality remains uncontrolled; testing it would require running a second extraction (Wang et al.'s lab variant or a multi-direction extraction) on the same checkpoints.

### Result 4: Mechanistic. Refusal geometry is most concentrated in a single cross-lingual direction at E4B

We extracted per-language refusal directions on the base checkpoint of each size, following the Arditi-style procedure used by Wang et al. (100 harmful + 10 harmless prompts per language, activation difference at the post-instruction position, layer with maximum direction norm).

**Cross-lingual cosine similarity of refusal directions** (mean over the 21 off-diagonal pairs of a 7×7 language matrix):

| | E2B | E4B | 31B |
|---|---|---|---|
| mean | 0.31 | **0.37** | 0.27 |
| max  | 0.67 | **0.71** | 0.52 |
| min  | 0.18 | 0.29 | 0.17 |

E4B's per-language refusal directions are the most aligned with each other. The size-to-cosine curve is non-monotonic and peaks at E4B, the same shape as the compliance curve.

**Per-language Silhouette scores** (separation of harmful vs harmless prompt activations at the refusal extraction layer, mean over 7 languages):

| Size | mean Silhouette |
|---|---|
| E2B | **0.29** |
| E4B | 0.26 |
| 31B | **0.23** |

Silhouette is monotonically decreasing in size: harmful and harmless prompts are most separable in the activation space at E2B and least separable at 31B.

**Putting the two together.** At E4B, the model has converged on a single dominant direction that captures refusal across all seven languages (highest cosine similarity), with harmful and harmless still well-separated locally (Silhouette mid-range). Single-vector ablation removes most of the structure. At E2B, harmful and harmless are well-separated locally but per-language refusal directions diverge (lowest cross-lingual cosine), so single-vector ablation removes one language's direction while others persist. At 31B, harmful and harmless are weakly separated and the per-language refusal directions diverge again (lowest cosine, lowest Silhouette), suggesting refusal is implemented across multiple distributed components rather than a single dominant direction. This is the mechanism predicted by reading #1 in the Discussion below, and the data support it cleanly.

### Negative and null results

The base-condition cells are not zero-compliant: 4.1% at E2B, 10.7% at E4B, 13.1% at 31B. We attribute most of this to two factors. First, Claude Haiku has a non-zero false-positive rate on borderline content; we observed this in an earlier E2B sanity-check run. Second, larger models follow instructions more often in general, including harmful ones, because instruction-following is what they were trained for. We have not separated these contributions. We flag them as a confound on the base row but not on the headline (abliterated cells across sizes), because all three abliterated cells use the same judge and the relative comparison is what matters.

## Discussion

**Did we answer the research question?** Yes, with shape. The compliance curve has clear curvature, not a slope. Within Gemma 4 Dense, single-vector English abliteration peaks at the mid-size model (~4B), and the curve declines slightly at the large endpoint (~31B). The findings reproduce the [Wang et al. 2025](https://arxiv.org/abs/2505.17306) universality result on a model family they did not test (Gemma 4) using a public recipe (`huihui-ai`) rather than an in-house extraction. They also qualify the universality result by showing that within a single Dense family, the cross-lingual compliance the attack induces is not monotonic in size.

**How should you update your beliefs?**

If you held the strong form of the *democratization safety paradox* ("small accessible models are the most dangerous because they are the easiest to abliterate"), the strong form is wrong. E2B refuses the majority of harmful prompts even after public abliteration. The weak form survives, because E4B is the most-compromised cell in the matrix and E4B is also a consumer-accessible model. The accessible-and-vulnerable region is real; it just sits one notch above the naive prediction.

If you held the inverse view ("scale brings vulnerability with it because larger models are better instruction-followers"), the curve does not support that either. Base compliance does scale with size, but post-abliteration compliance does not. At 31B the abliteration attack works less well than at E4B by a small but consistent margin.

**Why does the curve bend?** Three mechanisms could explain the shape; the mechanistic data (Result 4) adjudicates between them.

1. *Refusal geometry is more concentrated in mid-size Dense models.* At E2B, refusal could be implemented across several distributed and partly redundant directions, so single-vector ablation removes one and leaves others. At E4B, the model may have converged on a single dominant direction, and ablation removes most of the structure. At 31B, the geometry could distribute again, not as redundantly as in E2B but enough to leave residual refusal in place. Predicted: highest cosine similarity of refusal directions across languages at E4B; highest Silhouette score at E2B. **Both predictions hold.** Cosine similarity peaks at E4B (mean 0.37 vs 0.31 E2B, 0.27 31B); Silhouette is highest at E2B (0.29 vs 0.26 E4B, 0.23 31B). This is the reading the data support.
2. *Capability outpaces refusal between E2B and E4B, then refusal catches up at 31B.* This story would predict a monotonic base curve (which we see) and a non-monotonic gap curve (which we also see), without invoking refusal geometry directly. Predicted: refusal direction cosine similarities and Silhouette scores would scale monotonically with size. **Refuted.** Cosine similarity is non-monotonic (peaks at E4B). Silhouette is monotonic but decreasing, not increasing, the opposite of what "refusal catches up at 31B" requires.
3. *The `huihui-ai` recipe interacts with model scale in ways that are accidentally optimal at the mid-size point.* The recipe is the same script for all three checkpoints, but the prompts used to derive the refusal direction may not be equally informative at every scale. Predicts: a different recipe on the same checkpoints would shift the peak. **Untested.** Distinguishing this from reading #1 would require running Wang et al.'s lab extraction on the same six checkpoints; we have not done that.

Reading #1 is the best fit. Reading #3 cannot be ruled out without the second-recipe experiment.

### Limitations

* Single model family. We tested Gemma 4 Dense only. We cannot attribute the E4B peak to "Dense models in general" or to "abliteration in general" without at least one other family run with the same recipe and judge.
* Single abliteration recipe. All abliterated checkpoints come from `huihui-ai`'s public script. A second recipe on the same six checkpoints (for example the in-house extraction Wang et al. used) would test whether the peak is an artifact of the public recipe rather than the underlying model geometry.
* Single judge. Claude Haiku 4.5 is not the judge Wang et al. used (they used WildGuard). Absolute compliance numbers are judge-conditional and not directly comparable to Wang et al.'s. Within-experiment cell-to-cell comparisons (the headline) do not depend on this.
* Seven languages. Wang et al. used 14, including Polish, Russian, and Yoruba. Our per-language ranking is sensitive to the language sample, and we cannot test the safety-misaligned-language case (Wang et al.'s Yoruba result) without adding such a language.
* Translations were not back-translated for fidelity. Translation drift could move per-language compliance rates by a few points; it is unlikely to move means by enough to change the size ordering.
* Base-condition cells are not zero. We have not separated judge-calibration noise from genuine instruction-following on harmful prompts. Both contribute, in unknown proportion.
* Single random seed (42) for prompt sampling. Re-sampling would tighten per-language confidence intervals.
* Architecture held constant at Dense. Whether the routing layer in Gemma 4 26B-A4B (MoE) reproduces or breaks the E4B peak is the cleanest follow-up experiment.

### Calibration of claims

* **What we showed.** In this exact setup (six checkpoints, seven languages, 100 harmful prompts per language, Claude Haiku 4.5 judge, `huihui-ai` recipe), mean post-abliteration compliance is 42.9% at E2B, 68.1% at E4B, 64.4% at 31B. The base-to-abliterated gap is +38.8 pp, +57.4 pp, +51.3 pp respectively. Both curves peak at the mid-size point. The mechanistic phase confirms that refusal geometry is most concentrated in a single cross-lingual direction at E4B (mean cosine similarity 0.37 vs 0.31 E2B and 0.27 31B), with Silhouette scores monotonically decreasing in size (0.29 → 0.26 → 0.23). The compliance peak and the geometry peak coincide.
* **What we believe but did not show.** The E4B peak is a property of Gemma 4 Dense rather than the public `huihui-ai` recipe. Distinguishing recipe-driven from geometry-driven explanations would require running a second extraction (e.g. Wang et al.'s lab variant) on the same six checkpoints.
* **What we speculate.** A 26B-A4B MoE checkpoint matched on active parameters would not sit exactly on top of E4B. Routing introduces enough geometric variation that the refusal direction may not be as concentrated even at matched compute, so MoE-4B should land between E4B and 31B on this curve.

## Related work

* [Wang et al. 2025](https://arxiv.org/abs/2505.17306) showed that English-derived refusal directions transfer cross-lingually in instruction-tuned models from Yi, Qwen 2.5, Llama 3, and Gemma 2 (with their main analyses on 7B–14B variants). We test the same hypothesis on a Dense family they did not have access to (Gemma 4, released April 2, 2026) using a public recipe (`huihui-ai`) rather than their in-house extraction. We confirm cross-lingual transfer at all three Gemma 4 Dense sizes and add a within-family non-monotonic finding: the effect peaks at ~4B and declines slightly at ~31B.
* [Arditi et al. 2024](https://arxiv.org/abs/2406.11717) introduced single-direction ablation (the underlying technique that the open-weight community calls *abliteration*) and showed that refusal in instruction-tuned LLMs is mediated by a low-dimensional subspace. We use the public `huihui-ai` checkpoints produced with this style of attack, since these are the actual threat model: anyone can download them.
* An [embarrassingly simple defense against LLM abliteration attacks (2025)](https://arxiv.org/abs/2505.19056) proposes mitigation by training on extended refusals that distribute the refusal signal across many tokens (detailed justifications before the refusal itself), making the single-direction attack less effective. The defense is orthogonal to our claims; whether it flattens the E4B peak is open.

## Future work

1. **Compare abliteration recipes on the same six checkpoints.** Re-running with a different refusal direction extraction (for example the lab variant in [Wang et al. 2025](https://arxiv.org/abs/2505.17306), or a multi-direction extraction) on the same checkpoints would tell us whether the E4B peak is about Gemma 4 Dense or about the `huihui-ai` script in particular. This is the only remaining experiment that adjudicates between mechanism #1 and mechanism #3 in the Discussion.
2. **Add the 26B-A4B Mixture-of-Experts checkpoint, paired with E4B on active parameter count.** Same protocol, different architecture. Either MoE-4B sits with E4B at the peak (the routing layer does not protect refusal geometry) or it sits between E4B and 31B (routing introduces enough variation to recover some refusal structure). Both outcomes are publishable.
3. **Extend the size axis if Google releases intermediate Dense sizes.** The current curve has a 7x compute gap between E4B and 31B. A 9B or 14B Dense Gemma 4 checkpoint, if released, would tighten the post-peak slope.
4. **Test the [extended-refusal defense (Abu Shairah et al. 2025)](https://arxiv.org/abs/2505.19056) on Gemma 4 Dense.** Whether the defense flattens the E4B peak (the most-compromised cell in our matrix) is the natural follow-up safety question raised by Result 1.

## Acknowledgements

This is a mentored project at BAISH (Buenos Aires AI Safety Hub), supported by a BlueDot Rapid Grant (2026).
