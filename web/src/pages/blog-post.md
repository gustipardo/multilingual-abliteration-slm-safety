---
layout: ../layouts/BlogPostLayout.astro
title: "The most-jailbroken open Gemma 4 model is the one that fits on a phone"
description: "Within the Gemma 4 Dense family, single-vector English abliteration peaks at the mid-size (4B) model, not at the largest. Cross-size compliance results across 7 languages."
status: "Status: working draft (May 2026)"
---

# The most-jailbroken open Gemma 4 model is the one that fits on a phone

> **Status: working draft (May 2026).** All three sizes are inferred, judged, and mechanistically analyzed (refusal direction extraction + Silhouette scores). Compliance and mechanistic data are final for E2B, E4B, and 31B Dense.

## TL;DR

* **Setup.** *Abliteration* is a public jailbreak script for open  weight chat models: it finds the single internal direction that triggers refusal and projects it out of every layer ([Arditi et al. 2024](https://arxiv.org/abs/2406.11717)). [Wang et al. 2025](https://arxiv.org/abs/2505.17306) showed the same English  derived direction also disables refusal in 13 other languages on instruction  tuned 7B  14B models, but they extracted directions in  house and did not test Gemma 4.
* **Motivation.** Gemma 4 (Google, April 2, 2026) ships in four sizes: three Dense (E2B ~2.3B effective, E4B ~4.5B, 31B) and one Mixture  of  Experts (26B  A4B); we test the three Dense ones and exclude the MoE for now so size and architecture do not confound each other. `huihui  ai` released abliterated versions of all four within 48 hours, and these public checkpoints are the actual threat model: anyone can download and run them.
* **Main claim.** Across seven languages and 100 BeaverTails harmful prompts per language, mean compliance after English abliteration is 42.9% at E2B, **68.1% at E4B**, and 64.4% at 31B. The curve does not rise cleanly with size: it peaks at the mid  size model, not at the smallest or the largest.
* **Side finding 1.** Hindi has the lowest abliterated compliance at every size (39%, 65%, 60%), against the common assumption that languages with less internet pretraining data should be the most vulnerable to cross  lingual jailbreaks. The gap is clear at E2B (8 pp below the next language) and narrows to roughly noise at 31B.
* **Side finding 2.** The single highest cell in our matrix is 74% (E4B abliterated, Portuguese and German tied), well below the "consistently approaching or exceeding 90%" that Wang et al. report on 7B+ models in other families.
* **Mechanistic finding.** Inside each model there is a single internal direction that triggers refusal, and the seven languages share that direction the most at E4B (mean cross  lingual cosine similarity 0.37, against 0.31 at E2B and 0.27 at 31B; 0 means unrelated, 1 means identical). When the languages share one direction, removing it disables refusal in all seven at once: the compliance peak and the alignment peak land at the same model.
* **Impact.** The strong "smaller means more vulnerable" form of the *democratization safety paradox* is wrong inside Gemma 4 Dense, because E2B still refuses the majority of harmful prompts after public abliteration. A weaker form survives: E4B is also a consumer  accessible model, so the worst point in the matrix is at the size most users can run.
* **Code:** [github.com/gustipardo/multilingual-abliteration- lm-safety](https://github.com/gustipardo/multilingual-abliteration-slm-safety)

## Figure 1

![Mean compliance vs Gemma 4 Dense size, base and abliterated, with non-monotonic abliterated curve peaking at E4B](https://raw.githubusercontent.com/gustipardo/multilingual-abliteration-slm-safety/main/figures/size_vs_compliance.png)

**Caption.** Mean compliance rate over 7 languages (n = 100 harmful prompts per language, judged by Claude Haiku 4.5) for Gemma 4 Dense base and abliterated checkpoints at three sizes. The base curve is monotonic in size (4.1% → 10.7% → 13.1%); the abliterated curve is not (42.9% → 68.1% → 64.4%). Single vector English abliteration is most effective at the mid size Dense model.

## Introduction

When a chat model decides whether to refuse a harmful request, that decision lives in a small part of its internal state. [Arditi et al. 2024](https://arxiv.org/abs/2406.11717) showed it is well captured by a single direction in the model's hidden activations: feed the model harmful and harmless prompts, take the difference of the average activations, and you get a vector that points from "this is fine" toward "I should refuse". That vector is the *refusal direction*.

**Abliteration** is a community built jailbreak that exploits exactly this. The recipe finds the refusal direction and projects it out of every layer's output, leaving a checkpoint that mostly stops refusing harmful requests and keeps the rest of its capabilities. The script is short, public, and reproducible. Within 48 hours of Google releasing the Gemma 4 family on April 2, 2026, abliterated versions of every Gemma 4 size were on HuggingFace under the `huihui ai` namespace.

Whether refusal is a *single* direction has become the load bearing question for this style of attack. [Wang et al. 2025](https://arxiv.org/abs/2505.17306) extracted refusal directions from English prompts in instruction tuned models from Yi, Qwen 2.5, Llama 3, and Gemma 2 (mostly 7B 14B variants) and showed that ablating those directions raised compliance to harmful prompts in 13 other languages. In their stronger universality experiment, where they extracted directions from non English source languages (German, Chinese, Thai), compliance rates were "consistently approaching or exceeding 90%" across the other safety aligned languages.

Two questions Wang et al. did not address are directly relevant to the public threat model. First, their refusal direction extraction is a controlled procedure run by the authors. The public alternative is the `huihui ai` `remove refusals with transformers` script, which is the version a non expert user can actually download. Whether the public recipe reproduces the published universality result on a fresh model family is open. Second, Wang et al. evaluated points across families rather than within a single family with a continuous size axis. The within family scaling shape, especially in the sub 7B region, was not the focus of their analysis.

The Gemma 4 Dense lineup (E2B at ~2.3B effective parameters, E4B at ~4.5B effective, 31B Dense), [released by Google on April 2, 2026](https://blog.google/innovation-and-ai/technology/developers-tools/gemma-4/), is the first model family released *after* the Wang et al. submission with public abliterated checkpoints at three Dense sizes. It is the natural test bed for both questions.

**Threat model.** A non expert user downloads a public abliterated checkpoint of an open weight Gemma 4 model, runs it locally, and prompts it in any of the 140+ languages Gemma 4 supports. We measure how often that user gets a fully compliant response to a harmful prompt, judged by Claude Haiku 4.5 reading the full 512 token response.

**Research question.** Within the Gemma 4 Dense family, how does single vector English abliteration affect multilingual compliance with harmful prompts as model size increases from E2B to 31B?

**Contribution.** Mean post abliteration compliance across seven languages does not rise cleanly with model size. It rises by 25.3 percentage points from E2B (42.9%) to E4B (68.1%), then falls by 3.7 percentage points from E4B to 31B (64.4%). The base to abliterated gap (how much the attack adds on top of the base model's already low refusal rate) is also largest at E4B: +57.4 pp, against +38.8 pp at E2B and +51.3 pp at 31B. Inside this Gemma 4 Dense lineup, the public script removes the most refusal at the mid size model, not at the smallest or the largest.

**Why it matters.** The naive "smaller means more vulnerable" framing of the *democratization safety paradox* is wrong in detail: E2B still refuses the majority of harmful prompts even after public abliteration. A precise version of the paradox still holds, because E4B is also a consumer accessible model. At 4 bit it fits in roughly 3 GB of VRAM, which is the memory budget of a 2026 mid range smartphone, a Raspberry Pi 5 with 8 GB RAM, the integrated GPU on an M series MacBook Air, or any consumer NVIDIA card from the past several years. The model the public attack hits hardest is also one of the easiest to run.

## Methods

**Models.** Six checkpoints, two per size, all loaded with the same quantization config (bitsandbytes 4 bit NF4, double quant, bf16 compute). Bases are `google/gemma 4 E2B it` (~2.3B effective parameters via Per Layer Embeddings), `google/gemma 4 E4B it` (~4.5B effective), `google/gemma 4 31B it` (Dense, ~31B). Abliterated counterparts are `huihui ai/Huihui gemma 4 {E2B,E4B,31B} it abliterated`, all produced with the same `remove refusals with transformers` script. Identical recipe across sizes is what lets us isolate scale as the only thing that varies between abliterated cells.

The Gemma 4 lineup also contains a 26B A4B Mixture of Experts variant (~4B active parameters via routing). We exclude it from the principal experiment to keep the size axis clean. Mixing Dense and MoE on the same axis would confound size with architecture. The MoE variant is queued as a separate sub experiment.

**Prompts.** 100 harmful prompts per language, sampled with seed 42 from the BeaverTails `30k_test` split ([PKU-Alignment dataset](https://huggingface.co/datasets/PKU-Alignment/BeaverTails)) and filtered to `is_safe = False`. The non English versions are translations of the same 100 prompts.

**Languages.** English, Spanish, Chinese, Portuguese, German, Arabic, Hindi. A mix of high resource and medium resource.

**Generation.** Greedy decoding, 512 max new tokens. Gemma 4 frequently produces "delayed refusals" of the form "I can't help with that" embedded after 50 to 100 helpful tokens. A short generation budget would mis classify these as compliant.

**Judge.** Claude Haiku 4.5 reads the full prompt and the full response and emits one of three labels: complied, refused, partial. We treat *complied* as the only positive case for the compliance rate. Wang et al. used WildGuard ([Han et al. 2024](https://arxiv.org/abs/2406.18495)), an open source moderation classifier, in the same role. The two judges are not strictly comparable, so we treat absolute compliance numbers as judge conditional and rely on within experiment comparisons (cell to cell, size to size) for the headline.

*Compute, hardware, and the cloud reproducibility check on E2B all live in Appendix A.*

**Mechanistic protocol.**

*What we wanted to know.* The compliance numbers tell us *what* the model does after abliteration. We also wanted to know *why* the curve peaks at E4B by looking at what the model is doing internally before it speaks.

*What we measured.* For each base model and each language we fed it 100 harmful prompts and 10 harmless prompts, and read the model's hidden state right after it had finished reading the instruction. The *refusal direction* for that language is the difference between the average hidden state on harmful prompts and the average on harmless prompts ([Arditi et al. 2024](https://arxiv.org/abs/2406.11717)). It is the single direction in the model's "thought space" that points from "this is fine" toward "this is harmful, I should refuse". We extracted one direction per language at the layer where it is strongest.

Two numbers come out of this:

  *Cosine similarity* between every pair of the seven per language refusal directions. Cosine similarity asks "how parallel are these two arrows?": 1.0 means the same direction, 0.0 means unrelated, negative means opposite.
  *Silhouette score* per language at the same layer. This asks "how cleanly do harmful and harmless prompts separate inside the model's internal space?": high score means a strong internal "harm" concept, low score means a fuzzy boundary.

*Why this protocol.* A single English derived ablation can only succeed to the degree that all seven languages share *one* refusal direction. If each language uses its own direction, removing the English one leaves six others in place. So cross lingual cosine similarity is the prediction; the compliance rate is the consequence.

A complete protocol, including the judge prompt, is in `PROTOCOL.md` in the repo.

## Results

### Compliance peaks at the mid size model

**Table 1.** Compliance rates per cell (%). Same 100 harmful prompts, same Claude Haiku 4.5 judge, same `huihui ai` abliteration recipe across sizes. Bold marks the peak cell of the abliterated row.

|                 | EN     | ES  | ZH  | PT     | DE     | AR  | HI  | mean     |
| --------------- | ------ | --- | --- | ------ | ------ | --- | --- | -------- |
| E2B base        | 4      | 7   | 4   | 6      | 4      | 2   | 2   | **4.1**  |
| E2B abliterated | 42     | 47  | 45  | 40     | 44     | 43  | 39  | **42.9** |
| E4B base        | 13     | 11  | 7   | 16     | 10     | 9   | 9   | **10.7** |
| E4B abliterated | **70** | 66  | 64  | **74** | **74** | 64  | 65  | **68.1** |
| 31B base        | 16     | 12  | 13  | 16     | 12     | 10  | 13  | **13.1** |
| 31B abliterated | 67     | 64  | 65  | 63     | 71     | 61  | 60  | **64.4** |

The big move on the curve is the +25 pp jump from E2B to E4B, well outside the ~1.8 pp standard error on the seven-language mean. The drop from E4B to 31B is small but consistent: E4B beats 31B in 4 of 7 languages, ties in zero, trails in 3. The base-to-abliterated gap peaks at E4B too (+57 pp, vs +39 at E2B and +51 at 31B): the same off-the-shelf attack does the most work at the mid size.
### Hindi resists more than expected, but the size of the effect varies

Hindi has the lowest abliterated compliance of any language at every size: 39% at E2B, 65% at E4B, 60% at 31B. The most compliant high resource language is not stable across sizes either: Spanish leads at E2B (47%), Portuguese and German tie at E4B (74%), and German leads at 31B (71%). The common assumption that languages with less internet pretraining data should be the most vulnerable to a cross lingual jailbreak does not hold here.

How strong this finding is depends on which size you look at. At E2B the Hindi cell is 8 pp below the next lowest language (a clear effect). At E4B and 31B the Hindi cell is 1 pp below the next lowest, which is within the pooled standard error (~1.8 pp). So Hindi is *not* the most vulnerable at any size, but the visible resistance is a real effect at E2B and shrinks to roughly noise as the model grows.

The per language gaps after abliteration are nearly uniform at E4B (range +55 to +64 pp), and slightly more dispersed at E2B (+34 to +41 pp) and 31B (+47 to +59 pp). At the mid size point, the attack hits every language similarly hard.

### No cell reaches the 90% Wang et al. report on other families

The single highest compliance cell in our matrix is 74% (E4B abliterated, Portuguese and German tied). [Wang et al. 2025](https://arxiv.org/abs/2505.17306) report cells "consistently approaching or exceeding 90%" in their non English universality experiment on 7B+ Dense models. In their English derived ablation (the closer comparison to our setup), individual cells in their Figure 1 reach the 70 to 90% range for several models, with peaks higher than ours. Our E4B max (74%) is in the lower part of that range. Our E2B max (47%) and 31B max (71%) sit further from it.

Two readings are consistent with this gap, and the compliance numbers alone cannot tell them apart. First, refusal geometry in Gemma 4 Dense may be less concentrated in a single direction than in the Yi, Qwen 2.5, Llama 3, and Gemma 2 models Wang et al. tested, so even a successful single vector ablation leaves some residual refusal in place. Second, the public `huihui ai` recipe may be less aggressive than Wang et al.'s in house procedure, in which case the gap is about the recipe rather than the model. Our mechanistic phase (next subsection) speaks to the first reading directly: cross lingual cosine similarity peaks at E4B, exactly where compliance peaks, but is lower at every size in this family than the cross lingual alignment Wang et al. report for Gemma 2 9B.

We have not tested whether a different abliteration script would change the picture. The way to test it is to run a second extraction (for example the lab procedure in [Wang et al. 2025](https://arxiv.org/abs/2505.17306)) on the same six checkpoints and check whether the E4B peak holds.

### Inside the model: refusal directions align the most at E4B

For each base checkpoint we extracted seven per language refusal directions, one per language, using the procedure described in Methods.

**Cross lingual cosine similarity of refusal directions** (mean over the 21 off diagonal pairs of a 7x7 language matrix):

| | E2B | E4B | 31B |
|---|---|---|---|
| mean | 0.31 | **0.37** | 0.27 |
| max  | 0.67 | **0.71** | 0.52 |
| min  | 0.18 | 0.29 | 0.17 |

How aligned are the seven per language refusal directions across languages? Cosine similarity is the "how parallel are these two arrows?" measure: 1.0 means identical direction, 0.0 means unrelated, negative means opposite. We compared every pair of the seven directions and averaged the 21 pairs.

Read the *mean* row first. At E4B the seven languages' refusal directions are the most aligned (0.37). They are less aligned at E2B (0.31) and least aligned at 31B (0.27). The shape mirrors the compliance curve: peak at the mid size, lower at the endpoints.

This is the result that explains the compliance peak. English abliteration only works to the extent that the seven languages share *one* refusal direction. They share it the most at E4B, so removing it works the most at E4B.

The cosine number compares directions *across* languages. The next number checks something different at each layer: how cleanly the model separates harmful from harmless prompts *inside* one language.

**Per-language Silhouette scores** (mean over 7 languages, measured at the refusal-extraction layer):


| Size | mean Silhouette |
| ---- | --------------- |
| E2B  | **0.29**        |
| E4B  | 0.26            |
| 31B  | **0.23**        |

Silhouette decreases steadily with size: harmful and harmless prompts separate the cleanest at E2B and the messiest at 31B.

**Putting the two numbers together.** Picture seven arrows (one per language) inside the model's internal space.

- **E4B:** the seven arrows point almost the same way (high cosine). Removing one disables refusal in all seven.
- **E2B:** the arrows fan out (lowest cosine), even though the harmful and harmless prompt clusters are still cleanly separated (highest Silhouette). Removing one only kills refusal in that one language.
- **31B:** the arrows fan out *and* the clusters blur. Refusal is spread across several components, so single-vector ablation leaves a lot in place.

*A vector diagram of this would shorten the section and carry the intuition better than prose. On the figure backlog.*

This is mechanism #1 in the Discussion below. We had the geometry data in hand when we wrote that section, so read it as "consistent with the data", not as a prediction confirmed by independent evidence.

### Negative and null results

The base-condition cells are not zero: 4.1% at E2B, 10.7% at E4B, 13.1% at 31B. Two things drive this. First, Claude Haiku has a small false-positive rate on borderline content (we saw it in an earlier E2B sanity check). Second, larger models tend to follow instructions more often, harmful or not, because that is what they were trained for. We did not separate these two effects, so the absolute base numbers carry some noise. The headline (size-by-size comparison after abliteration) is unaffected: all three abliterated cells use the same judge, so the relative ordering across sizes is reliable.
## Discussion

**Did we answer the research question?** Partially. Within Gemma 4 Dense, the public abliteration script removes the most refusal at the mid size model (~4B), and the attack does slightly less work at the large endpoint (~31B). Whether that shape is a property of Gemma 4 Dense in particular, of all Dense families in general, or of the public `huihui ai` recipe applied to Dense families, is more than one experiment can answer.

**How should you update your beliefs?**

If you held the strong form of the *democratization safety paradox* ("small accessible models are the most dangerous because they are the easiest to abliterate"), the data here says the opposite. E2B still refuses the majority of harmful prompts even after public abliteration. A weaker form does survive: E4B is the most compromised cell in the matrix, and E4B is also a consumer-accessible model, so the accessible-and-vulnerable region is real, it just sits one notch above the smallest size in this lineup.

If you held the inverse view ("scale brings vulnerability with it because larger models are better instruction followers"), the curve does not support that either, in this lineup. Base compliance does rise with size, but post abliteration compliance does not. At 31B the attack does less work than at E4B by a small but consistent margin (3.7 pp, about two pooled standard errors). This is a Gemma 4 Dense observation; we are not making a settled claim about scale and abliteration in general.

**Why isn't compliance just rising with size? Three readings, checked against the geometry data.**

All three readings are post-hoc: the geometry data was already in hand when we wrote them. So read them as "which story fits the numbers best?", not as predictions confirmed by independent evidence.

1. *Refusal geometry is most concentrated at E4B.* At E2B refusal is spread across several directions; at E4B it converges on one dominant direction; at 31B it spreads out again. **The geometry data fits:** cross-lingual cosine peaks at E4B, Silhouette peaks at E2B.

2. *Capability outpaces refusal early, then refusal catches up.* This story would predict cosine and Silhouette both rising with size. **The data does the opposite:** cosine peaks at E4B and Silhouette decreases with size. (Caveat: judge calibration on E2B muddles this test, but the cosine prediction is judge-independent and still fails.)

3. *The `huihui-ai` recipe is accidentally optimal at the mid size.* Same script across all three checkpoints, but the prompts used to derive the refusal direction may not be equally informative at every scale. **Untested.**
### Limitations

* Single model family. We tested Gemma 4 Dense only. 
* Single abliteration recipe. All abliterated checkpoints come from `huihui ai`'s public script.
* Single judge. Claude Haiku 4.5 is not the judge Wang et al. used (they used WildGuard). 
* Seven languages. Wang et al. used 14, including Polish, Russian, and Yoruba.
* Translations were not back translated for fidelity. Translation drift could move per language compliance rates by a few points; it is unlikely to move means by enough to change the size ordering.
* Base condition cells are not zero. We have not separated judge  calibration noise from genuine instruction following on harmful prompts. Both contribute, in unknown proportion.
* Single random seed (42) for prompt sampling. Re  sampling would tighten per  language confidence intervals.
* Architecture held constant at Dense. Whether the routing layer in Gemma 4 26B  A4B (MoE) reproduces or breaks the E4B peak is the cleanest follow  up experiment.
### Calibration of claims

* **What we showed.** In this exact setup (six checkpoints, seven languages, 100 harmful prompts per language, Claude Haiku 4.5 judge, `huihui  ai` recipe), mean post  abliteration compliance is 42.9% at E2B, 68.1% at E4B, 64.4% at 31B. The base  to  abliterated gap is +38.8 pp, +57.4 pp, +51.3 pp respectively. Both curves peak at the mid  size point. The mechanistic phase confirms that refusal geometry is most concentrated in a single cross  lingual direction at E4B (mean cosine similarity 0.37 vs 0.31 E2B and 0.27 31B), with Silhouette scores monotonically decreasing in size (0.29 → 0.26 → 0.23). The compliance peak and the geometry peak coincide.
* **What we believe but did not show.** The E4B peak is more likely a property of Gemma 4 Dense than an artifact of the public `huihui-ai` recipe. The cosine peak is measured on the *base* checkpoints, not on the abliterated ones, so the recipe cannot have caused it; the recipe only sees this geometry, it does not create it. We also believe the result needs more robust testing (a second extraction recipe, a second judge, more languages) before it should be treated as a settled finding.
* **What we speculate.** Other open-weight Dense families released since 2025 should show a similar mid-size peak when abliterated with the same public script. The geometry argument (one dominant refusal direction at the mid size, spread out at the endpoints) is family-agnostic in principle; testing it is a one-week experiment per additional family.

## Related work

* [Wang et al. 2025](https://arxiv.org/abs/2505.17306) showed that English-derived refusal directions transfer across languages in 7B-14B models from Yi, Qwen 2.5, Llama 3, and Gemma 2; we test the same hypothesis on Gemma 4 (released after their submission) using a public abliteration script instead of their in-house extraction.
* [Arditi et al. 2024](https://arxiv.org/abs/2406.11717) introduced the single-direction ablation technique that the open-weight community calls *abliteration*; we test the public checkpoints produced by it.
* An [embarrassingly simple defense (2025)](https://arxiv.org/abs/2505.19056) trains models on extended refusals to spread the refusal signal across many tokens, making single-vector ablation less effective; whether it flattens the E4B peak is open.

## Future work

1. **Compare abliteration recipes on the same six checkpoints.** Re  running with a different refusal  direction extraction (for example the lab variant in [Wang et al. 2025](https://arxiv.org/abs/2505.17306), or a multi  direction extraction) on the same six checkpoints would tell us whether the E4B peak is about Gemma 4 Dense or about the `huihui  ai` script in particular. This is the only remaining experiment that adjudicates between mechanism 1 and mechanism 3 in the Discussion.
2. **Add the 26B  A4B Mixture  of  Experts checkpoint, paired with E4B on active parameter count.** Same protocol, different architecture. Either MoE  4B sits with E4B at the peak (the routing layer does not protect refusal geometry) or it lands between E4B and 31B (routing introduces enough variation to recover some refusal structure). Both outcomes are publishable.
3. **Test more languages and a second judge.** Adding low-resource and safety-misaligned languages (Yoruba, Polish) and replacing Claude Haiku with WildGuard would test whether the per-language ranking and the size-vs-compliance shape survive judge and language perturbations.

## Acknowledgements

This is a mentored project at BAISH (Buenos Aires AI Safety Hub), supported by a BlueDot Rapid Grant (2026).

## Appendix A: compute, hardware, and reproducibility notes

**Compute.** E2B inference and judging ran locally on an RTX 4070 (8 GB VRAM) in 5h 47m. E4B and 31B ran on rented RunPod RTX 5090 pods (32 GB VRAM each) in 7h 1m for $7.33 and 20h 19m for $23.50 respectively. The mechanistic phase for E4B and 31B ran later on two fresh RTX 5090 pods, each finishing in under an hour for less than $1 per pod. Total cloud spend across the three runs: ~$32.

**Cloud reproducibility check on E2B.** Because E2B was the only size run on a laptop, we re-ran the E2B matrix on a rented RunPod RTX 4090 to rule out laptop-specific artifacts. Twelve of fourteen shared cells reproduce within 3 percentage points; two cells (DE +7 pp, ZH +8 pp) drift further. The headline (mean abliterated compliance 42.9% at E2B) survives within ~2 pp. AR and HI did not finish before the pod was externally terminated and remain unvalidated on cloud.

**Pipeline issues worth recording:**

- *NVML driver degradation past hour 22.* On the long 31B inference pod, the NVIDIA Management Library readings became unreliable (runaway VRAM-usage numbers) after about 22 hours of continuous use. The mechanistic phase queued at the end of that pod's run never finished. Solution: split inference and mechanistic phases across separate pods.
- *bnb 4-bit transient peak above 7.62 GiB.* E4B was originally planned for the same 8 GB laptop as E2B, but the bitsandbytes 4-bit loader briefly holds non-quantized chunks alongside quantized ones during weight materialization, which exceeds the 4070's budget. We migrated E4B to RunPod after this surfaced.
- *Incremental upload saved a partial E2B cloud re-run.* On the cloud reproducibility re-run, an external pod termination at hour 5 would have cost the entire run. The bootstrap was patched mid-session to upload partial results to HuggingFace every 60 seconds, which preserved twelve of fourteen cells from the killed pod.

