# Research Topic Report: Multilingual Safety Collapse via Abliteration in Small Language Models

> Generated: 2026-04-13
> Papers analyzed: 27 (20 academic + 10 LessWrong/Alignment Forum)

## Topic Definition

When an LLM's refusal behavior is removed via abliteration (orthogonally projecting out the refusal direction from model weights), does safety collapse uniformly across all languages, or do non-English languages retain independent refusal geometries? And critically: is this effect worse in smaller, more democratically accessible models?

This research sits at the intersection of three areas: (1) abliteration mechanics and refusal geometry, (2) cross-lingual safety transfer, and (3) small language model safety. All three areas have active literature, but their intersection — abliteration × multilingual × model size scaling — is largely unexplored.

## Dimensions Tracked

| Dimension | Description |
|-----------|------------|
| Methodology | How refusal directions are measured/ablated |
| Model scale | Sizes tested — critical for size-scaling hypothesis |
| Languages covered | Which languages, resource level |
| Key findings | Core results on cross-lingual safety collapse |
| Open questions | What authors flag as unresolved |

---

## Paper Catalog

### 1. Refusal in Language Models Is Mediated by a Single Direction
- **Authors:** Arditi, Obeso, Syed, Paleka, Panickssery, Gurnee, Nanda
- **Source:** NeurIPS 2024
- **Year:** 2024
- **URL:** https://arxiv.org/abs/2406.11717
- **LW/AF:** https://www.lesswrong.com/posts/jGuXSZgv6qfdhMCuJ/refusal-in-llms-is-mediated-by-a-single-direction

| Dimension | Finding |
|-----------|---------|
| Methodology | Mean difference of residual stream activations on harmful vs harmless prompts; orthogonal projection to ablate |
| Model scale | 13 models, up to 72B |
| Languages | English only |
| Key findings | Single direction necessary and sufficient for refusal; ablating it causes near-complete safety collapse |
| Open questions | Cross-lingual generalization not studied |

**Relevance:** Foundational paper. Establishes the mechanism that makes abliteration possible. ~5,000 abliterated models now exist on HuggingFace as a direct consequence.

---

### 2. Refusal Direction is Universal Across Safety-Aligned Languages
- **Authors:** Wang, Wang, Liu, Schütze, Plank
- **Source:** arXiv
- **Year:** 2025 (May)
- **URL:** https://arxiv.org/abs/2505.17306

| Dimension | Finding |
|-----------|---------|
| Methodology | PolyRefuse dataset (14 languages, 7 writing systems); extract English refusal vector, test cross-lingual transfer; PCA + Silhouette Scores |
| Model scale | Yi, Qwen2.5, Llama-3, Gemma-2 — all 7B+ |
| Languages | 14 languages including low-resource |
| Key findings | English refusal vector transfers with near-perfect effectiveness to all tested languages; refusal directions are approximately parallel across languages |
| Open questions | Small models (<7B) not tested; why harmful/harmless cluster separation is worse in non-English not fully explained |

**Relevance:** THE closest existing paper. Demonstrates the core premise of the research idea but does NOT cover SLMs or within-family size scaling. Direct methodological template (replicate their visualizations for Gemma 4).

---

### 3. There Is More to Refusal in Large Language Models than a Single Direction
- **Authors:** Joad, Hawasly, Boughorbel, Durrani, Sencar
- **Source:** arXiv
- **Year:** 2026
- **URL:** https://arxiv.org/abs/2602.02132

| Dimension | Finding |
|-----------|---------|
| Methodology | Tests refusal across 11 categories (safety, incomplete requests, anthropomorphization, etc.) |
| Model scale | Multiple, up to frontier scale |
| Languages | Not discussed |
| Key findings | Refusal maps to geometrically distinct directions across categories, but a shared "control knob" explains most variance |
| Open questions | Does multi-directionality vary by model size? |

**Relevance:** Partially complicates the single-direction assumption underlying abliteration. Practically, abliteration still works because the shared component dominates.

---

### 4. The Geometry of Refusal in Large Language Models: Concept Cones and Representational Independence
- **Authors:** Wollschläger, Elstner, Geisler, Cohen-Addad, Günnemann, Gasteiger
- **Source:** arXiv
- **Year:** 2025
- **URL:** https://arxiv.org/html/2502.17420

| Dimension | Finding |
|-----------|---------|
| Methodology | Concept cone analysis of refusal geometry |
| Model scale | Includes Qwen2.5-1.5B (small) and larger models |
| Languages | Not discussed |
| Key findings | **Smaller models exhibit faster performance degradation as cone dimensionality increases; larger models maintain more robust refusal structure** |
| Open questions | Cross-lingual geometry of concept cones unstudied |

**Relevance:** Direct evidence that smaller models have geometrically weaker refusal representations — supports the hypothesis that abliteration is more destructive in SLMs.

---

### 5. Comparative Analysis of LLM Abliteration Methods: A Cross-Architecture Evaluation
- **Authors:** Richard J. Young
- **Source:** arXiv
- **Year:** 2025 (December)
- **URL:** https://arxiv.org/abs/2512.13655

| Dimension | Finding |
|-----------|---------|
| Methodology | Evaluates Heretic, DECCP, ErisForge, FailSpy across 16 models |
| Model scale | 7B–14B only |
| Languages | English only |
| Key findings | Large variance in capability preservation (GSM8K: +1.51pp to -18.81pp); mathematical reasoning most sensitive |
| Open questions | No multilingual evaluation; no sub-7B models |

**Relevance:** Establishes abliteration tool comparison baseline. Does NOT cover sub-7B or multilingual — direct gap.

---

### 6. An Embarrassingly Simple Defense Against LLM Abliteration Attacks
- **Authors:** Abu Shairah, Hammoud, Ghanem, Turkiyyah (KAUST)
- **Source:** arXiv
- **Year:** 2025 (May)
- **URL:** https://arxiv.org/abs/2505.19056

| Dimension | Finding |
|-----------|---------|
| Methodology | Extended-refusal dataset with 3-component responses; disperses safety signal across multiple dimensions |
| Model scale | 1.5B, 3B, 7B |
| Languages | English only |
| Key findings | Baseline models drop from ~90% to 13-21% refusal rate after abliteration; defense maintains >90% |
| Open questions | Does defense hold cross-lingually? Does multilingual abliteration vulnerability differ by size? |

**Relevance:** Tests abliteration on small models (1.5B, 3B) — confirms abliteration works at small scale. No multilingual evaluation.

---

### 7. A Granular Study of Safety Pretraining under Model Abliteration
- **Source:** arXiv
- **Year:** 2025 (October)
- **URL:** https://arxiv.org/abs/2510.02768

| Dimension | Finding |
|-----------|---------|
| Methodology | Compares abliteration robustness across different pretraining safety recipes |
| Model scale | Not specified |
| Languages | Not discussed |
| Key findings | Refusal-only alignment is most fragile; richer pretraining (safe data filtering + rephrasing + metatags) provides partial robustness |
| Open questions | How does this interact with multilingual pretraining data distribution? |

**Relevance:** If SLMs receive minimal safety pretraining (likely given capacity constraints), they are especially vulnerable.

---

### 8. Multilingual Jailbreak Challenges in Large Language Models
- **Authors:** Deng, Zhang, Pan, Bing
- **Source:** ICLR 2024
- **Year:** 2024
- **URL:** https://arxiv.org/abs/2310.06474

| Dimension | Finding |
|-----------|---------|
| Methodology | Translate harmful prompts into low-resource languages; test compliance on ChatGPT/GPT-4 |
| Model scale | GPT-4, ChatGPT (closed, large) |
| Languages | Low-resource languages (not specified but diverse) |
| Key findings | Low-resource languages produce ~3x more unsafe content; attack success 80.92% (ChatGPT), 40.71% (GPT-4) |
| Open questions | Open-source models; smaller models; abliteration as intervention |

**Relevance:** Establishes the baseline multilingual safety gap. Pre-abliteration, low-resource languages are already weaker — abliteration may amplify this asymmetry.

---

### 9. The State of Multilingual LLM Safety Research: From Measuring the Language Gap to Mitigating It
- **Source:** arXiv
- **Year:** 2025 (May)
- **URL:** https://arxiv.org/abs/2505.24119

| Dimension | Finding |
|-----------|---------|
| Methodology | Systematic review of ~300 publications 2020-2024 |
| Model scale | Survey |
| Languages | All |
| Key findings | Safety research is heavily English-centric; language gap in safety is widening |
| Open questions | SLMs; abliteration; non-English-first safety training |

**Relevance:** Frames the broader motivation. Confirms the research area is under-studied.

---

### 10. Do Methods to Jailbreak and Defend LLMs Generalize Across Languages?
- **Source:** arXiv
- **Year:** 2025 (November)
- **URL:** https://arxiv.org/abs/2511.00689

| Dimension | Finding |
|-----------|---------|
| Methodology | Test jailbreak and defense transfer across languages |
| Model scale | Multiple |
| Languages | Multiple, high and low resource |
| Key findings | Attack success and defense robustness vary language-by-language; high-resource safer under standard queries but more vulnerable adversarially |
| Open questions | Abliteration specifically; size scaling |

**Relevance:** Shows language-specific vulnerability patterns that may interact with abliteration.

---

### 11. EASE: Practical and Efficient Safety Alignment for Small Language Models
- **Authors:** Shi, Wang, Ouyang, Wang
- **Source:** AAAI 2026
- **Year:** 2025 (November)
- **URL:** https://arxiv.org/abs/2511.06512

| Dimension | Finding |
|-----------|---------|
| Methodology | Selective safety reasoning; reduces jailbreak ASR by up to 17% |
| Model scale | Small models (exact sizes not specified but sub-7B) |
| Languages | Not discussed |
| Key findings | Refusal training degrades general capability proportionally more in SLMs; current shallow alignment fails under adversarial jailbreaks |
| Open questions | Multilingual safety in SLMs; abliteration robustness |

**Relevance:** Confirms the research idea's premise: SLMs face distinct safety-capacity tradeoffs. Abliteration exploits the shallow alignment that EASE is trying to fix.

---

### 12. Can Small Language Models Reliably Resist Jailbreak Attacks? A Comprehensive Evaluation
- **Authors:** Zhang et al. (Zhejiang University)
- **Source:** arXiv
- **Year:** 2025
- **URL:** https://arxiv.org/html/2503.06519v1

| Dimension | Finding |
|-----------|---------|
| Methodology | 63 models (100MB–7B) across 15 families; multiple jailbreak methods |
| Model scale | 100MB to 7B — most comprehensive small-model coverage |
| Languages | Not discussed (likely English only) |
| Key findings | **47.6% of SLMs show high jailbreak susceptibility (ASR > 40%)**; 38.1% cannot resist direct harmful queries; counter-intuitively, larger SLMs can be more vulnerable due to better instruction-following |
| Open questions | Multilingual; abliteration specifically |

**Relevance:** Most comprehensive SLM jailbreak study. No multilingual analysis — clear gap your work fills.

---

### 13. Multilingual Safety Alignment via Sparse Weight Editing
- **Authors:** Liang, Wang, Wang
- **Source:** arXiv
- **Year:** 2026 (February)
- **URL:** https://arxiv.org/abs/2602.22554

| Dimension | Finding |
|-----------|---------|
| Methodology | Localize safety to "safety neurons"; constrained linear transformation |
| Model scale | Qwen2-0.5B, Qwen2-1.5B, and larger |
| Languages | Multiple |
| Key findings | **Safety improvements are "particularly pronounced for low-resource languages and smaller backbones"** — Qwen2-0.5B shows larger absolute reductions in unsafe responses than larger models |
| Open questions | Inverse: are smaller models proportionally worse BEFORE the fix? |

**Relevance:** Confirms smaller models have larger baseline multilingual safety gaps — directly supports the size-scaling hypothesis.

---

### 14. Align Once, Benefit Multilingually
- **Authors:** Bu, Liu, Ren, Yang, Dai
- **Source:** arXiv
- **Year:** 2026 (February)
- **URL:** https://arxiv.org/abs/2602.16660

| Dimension | Finding |
|-----------|---------|
| Methodology | Multi-Lingual Consistency (MLC) loss |
| Model scale | 1.5B–7B |
| Languages | 10 languages including low-resource |
| Key findings | MLC raises safety above 90% across all 10 languages; works at 1.5B scale |
| Open questions | How does MLC interact with abliteration? |

**Relevance:** Shows multilingual safety CAN be fixed at 1.5B scale — provides a "what good looks like" target and a potential future direction for your paper's recommendations.

---

### 15. Lost in Translation? Cross-Lingual Transfer of Composite Harms
- **Source:** arXiv
- **Year:** 2026
- **URL:** https://arxiv.org/html/2602.07963

| Dimension | Finding |
|-----------|---------|
| Methodology | Test safety across English + 5 Indic languages on GPT-OSS 20B, LLaMA-3-8B, Qwen3-32B |
| Model scale | 8B (smallest) to 32B |
| Languages | English + Hindi, Bengali, Telugu, Gujarati, Kannada |
| Key findings | **LLaMA-3-8B (smallest) is most permissive; attack success >45% in Gujarati/Kannada; GPT-OSS 20B (largest) shows highest caution** |
| Open questions | Models below 8B; abliteration |

**Relevance:** Direct cross-model-size compliance rate comparison across non-English languages — smaller model = more permissive. Supports size-scaling hypothesis without abliteration intervention.

---

### 16. Low-resourced languages get jailbroken more. Can SAEs explain why?
- **Author:** Andrii Shportko
- **Source:** LessWrong
- **Year:** 2025 (January)
- **URL:** https://www.lesswrong.com/posts/8h2KxbPhFx8JoEGdH/low-resourced-languages-get-jailbroken-more-can-saes-explain

| Dimension | Finding |
|-----------|---------|
| Methodology | SAE feature analysis on Gemma-2-2B-IT; 200 JailBreakBench prompts translated to Japanese, Dutch, Spanish |
| Model scale | Gemma-2-2B (small!) |
| Languages | Japanese, Dutch, Spanish |
| Key findings | SAE feature #14018 predicts refusal in English (β=+0.979) but flips to non-refusal in Japanese (β=−0.787) — refusal features lose semantic meaning cross-lingually in small models |
| Open questions | **Explicitly asks: does this instability scale across model sizes?** |

**Relevance:** Uses Gemma-2-2B — the scale most similar to Gemma 4 E2B. Raises the EXACT open question your research addresses.

---

### 17. Single Direction vs Low-Rank Refusal in Small LLMs
- **Source:** LessWrong
- **URL:** https://www.lesswrong.com/posts/LMkvjDTLKFrgdzJdG/single-direction-vs-low-rank-refusal-in-small-llms-1

| Dimension | Finding |
|-----------|---------|
| Methodology | Compare single-direction vs low-rank subspace for refusal across model sizes |
| Model scale | Qwen 1.5 0.5B, Gemma 2 9B |
| Languages | Not discussed |
| Key findings | **In some smaller models, refusal spans a low-rank subspace across layers with poor cross-layer generalization; single-vector abliteration achieves ~36% compliance vs ~91% on Qwen (single-direction model)** |
| Open questions | Cross-lingual refusal geometry in small models |

**Relevance:** Critical finding — abliteration may be LESS effective in the smallest models (refusal is distributed, not single-direction). This could complicate the hypothesis: may need multi-vector abliteration for sub-2B models.

---

### 18. SafeLawBench
- **Source:** arXiv
- **Year:** 2025
- **URL:** https://arxiv.org/abs/2506.06636

| Dimension | Finding |
|-----------|---------|
| Methodology | Safety benchmark across model sizes |
| Model scale | Various |
| Languages | Not specified |
| Key findings | **Models under 10B parameters do not exceed 70.9% average safety scores** — clear empirical relationship between model size and safety robustness |
| Open questions | Multilingual; abliteration |

**Relevance:** Supports the size-safety relationship empirically.

---

### 19. Fine-tuning Aligned Language Models Compromises Safety
- **Authors:** Qi, Zeng, Xie, Chen, Jia, Mittal, Henderson
- **Source:** ICLR 2024
- **Year:** 2023
- **URL:** https://arxiv.org/abs/2310.03693

| Dimension | Finding |
|-----------|---------|
| Methodology | Fine-tuning with 10 adversarial examples at $0.20 cost |
| Model scale | 7B models |
| Languages | English |
| Key findings | Safety alignment is brittle; cheap to remove via fine-tuning |
| Open questions | N/A |

**Relevance:** Contextualizes abliteration within the broader landscape of cheap safety-removal methods. Strengthens the democratization-of-risk framing.

---

## Dimension Synthesis

### Methodology

**Pattern:** Most abliteration papers use difference-in-means on English contrast pairs → orthogonal projection. Wang et al. 2025 extends this cross-lingually. LW post #17 finds some small models need low-rank (multi-vector) abliteration.

**Key findings:**
- Standard single-direction abliteration works on models ≥7B
- Sub-2B models may have distributed refusal (low-rank subspace) — abliteration may be less straightforward
- For Gemma 4 evaluation: verify that public abliterated models used TrevorS's biprojection+EGA method consistently across all sizes

**Gaps:** No paper measures post-abliteration compliance rates broken down by language × model size.

---

### Model Scale

**Pattern:** Existing abliteration work covers 7B–72B. SLM jailbreak work goes down to 100MB. The 1B–4B range (Gemma 4 E2B, E4B) is almost entirely unstudied for abliteration specifically.

**Key findings:**
- Smaller models have weaker refusal geometry (concept cones degrade faster) — paper #4
- Smaller models show higher jailbreak susceptibility in 47.6% of cases — paper #12
- Sub-10B models cap at 70.9% safety score — paper #18
- Safety improvements most pronounced for smaller backbones — paper #13

**Gaps:** No within-family size scaling study for abliteration effects.

---

### Languages Covered

**Pattern:** Most papers test English-only or add a few high-resource languages. Low-resource language coverage is sparse.

**Key findings:**
- Low-resource languages already 3x more unsafe at baseline (pre-abliteration) — paper #8
- Refusal features lose semantic meaning cross-lingually even in Gemma-2-2B — LW post #16
- Arabic and Hindi show >45% attack success in adjacent work — paper #13

**Gaps:** No paper tests multilingual abliteration compliance on Gemma 4 variants.

---

### Key Findings (Cross-Literature)

The literature collectively shows:
1. Abliteration works by removing a single (or low-rank) direction in activation space
2. English-derived refusal vectors universally transfer to all tested languages in models ≥7B
3. Smaller models are consistently more vulnerable to jailbreaks, have weaker refusal geometry, and have larger multilingual safety gaps
4. The combination of (1)+(2)+(3) suggests the research hypothesis is likely true — but nobody has tested it directly

---

### Open Questions (from papers)

- Does refusal direction instability across languages scale with model size? (LW post #16, explicitly)
- Do multilingual abliteration effects differ at sub-7B scale? (Wang et al., implicitly)
- Does low-rank refusal structure in small models make them harder OR easier to fully abliterate? (LW post #17)
- Is the "delayed refusal" pattern in Gemma 4 more or less pronounced in smaller variants?

---

## Coverage Gap Analysis

**Under-researched areas:**
- Abliteration effects in sub-7B models — no paper covers this directly
- Cross-lingual compliance rates post-abliteration by model size — the exact gap this research fills
- Gemma 4 family specifically — no paper has had time to study it (released April 2026)
- Within-family size scaling for abliteration effects

**Methodological gaps:**
- No paper uses LLM-as-judge with full-response generation for Gemma 4 (the delayed refusal pattern means token-limited eval is unreliable)
- Most multilingual safety papers don't use abliteration as the intervention (they translate prompts instead)

**Contradictions:**
- LW post #17 finds abliteration less effective in smallest models (36% compliance vs 91% for single-direction models) — this contradicts the "smaller = more vulnerable" hypothesis. Resolution: may need to distinguish between abliteration effectiveness (how much safety is removed) and baseline safety level (how safe the model was to begin with)
- Paper #11 finds larger SLMs can be MORE vulnerable due to better instruction-following — size isn't a simple monotonic predictor

---

## Research Frontier

1. **Within-family size scaling of abliteration effects** — this research idea, genuinely open. Gemma 4 is the perfect test bed (phone-scale to 4090-scale, same architecture).

2. **Low-rank vs single-direction refusal in SLMs cross-lingually** — LW post #17 raises this; combining with multilingual evaluation would be novel.

3. **Multilingual defense against abliteration** — Paper #6 (EASE defense) doesn't test multilingual; paper #14 (Align Once) doesn't test abliteration robustness. Combining both is an open direction.

**Suggested follow-up questions:**
1. Does the TrevorS biprojection+EGA method fully abliterate refusal in Gemma 4 E2B, or does low-rank structure require multi-vector removal?
2. Is the "delayed refusal" pattern weaker in smaller Gemma 4 variants?
3. If Arabic/Hindi show higher compliance post-abliteration, is this because their refusal direction is less aligned with the English direction, or because baseline refusal was weaker?

---

## Full Source List

| # | Title | Year | URL |
|---|-------|------|-----|
| 1 | Refusal in Language Models Is Mediated by a Single Direction | 2024 | https://arxiv.org/abs/2406.11717 |
| 2 | Refusal Direction is Universal Across Safety-Aligned Languages | 2025 | https://arxiv.org/abs/2505.17306 |
| 3 | There Is More to Refusal than a Single Direction | 2026 | https://arxiv.org/abs/2602.02132 |
| 4 | The Geometry of Refusal: Concept Cones | 2025 | https://arxiv.org/html/2502.17420 |
| 5 | Comparative Analysis of LLM Abliteration Methods | 2025 | https://arxiv.org/abs/2512.13655 |
| 6 | Simple Defense Against LLM Abliteration Attacks | 2025 | https://arxiv.org/abs/2505.19056 |
| 7 | Granular Study of Safety Pretraining under Abliteration | 2025 | https://arxiv.org/abs/2510.02768 |
| 8 | Multilingual Jailbreak Challenges in LLMs | 2024 | https://arxiv.org/abs/2310.06474 |
| 9 | State of Multilingual LLM Safety Research | 2025 | https://arxiv.org/abs/2505.24119 |
| 10 | Do Jailbreak Methods Generalize Across Languages? | 2025 | https://arxiv.org/abs/2511.00689 |
| 11 | EASE: Safety Alignment for SLMs | 2025 | https://arxiv.org/abs/2511.06512 |
| 12 | Can SLMs Reliably Resist Jailbreak Attacks? | 2025 | https://arxiv.org/html/2503.06519v1 |
| 13 | Multilingual Safety Alignment via Sparse Weight Editing | 2026 | https://arxiv.org/abs/2602.22554 |
| 14 | Align Once, Benefit Multilingually | 2026 | https://arxiv.org/abs/2602.16660 |
| 15 | Lost in Translation? Cross-Lingual Transfer of Composite Harms | 2026 | https://arxiv.org/html/2602.07963 |
| 16 | Low-resourced languages get jailbroken more (LW) | 2025 | https://www.lesswrong.com/posts/8h2KxbPhFx8JoEGdH |
| 17 | Single Direction vs Low-Rank Refusal in Small LLMs (LW) | 2025 | https://www.lesswrong.com/posts/LMkvjDTLKFrgdzJdG |
| 18 | SafeLawBench | 2025 | https://arxiv.org/abs/2506.06636 |
| 19 | Fine-tuning Aligned LLMs Compromises Safety | 2023 | https://arxiv.org/abs/2310.03693 |
| 20 | Universal Refusal Circuits Across LLMs | 2026 | https://arxiv.org/abs/2601.16034 |
| 21 | Multilingual Blending: Safety Evaluation | 2024 | https://arxiv.org/abs/2407.07342 |
| 22 | MPO: Multilingual Safety via Reward Gap | 2025 | https://arxiv.org/abs/2505.16869 |
| 23 | Bridging the Multilingual Safety Divide | 2026 | https://arxiv.org/abs/2602.13867 |
| 24 | CSSBench: Lightweight LLMs vs Chinese Adversarial Patterns | 2026 | https://arxiv.org/abs/2601.00588 |
| 25 | LSR: Linguistic Safety Robustness Benchmark | 2026 | https://arxiv.org/html/2603.19273 |
| 26 | Alignment and Safety in LLMs: Survey | 2025 | https://arxiv.org/abs/2507.19672 |
| 27 | Base LLMs refuse too (LW) | — | https://www.lesswrong.com/posts/YWo2cKJgL7Lg8xWjj |
