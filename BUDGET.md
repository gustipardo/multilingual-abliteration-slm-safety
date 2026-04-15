# Project Budget — Blue Dot Application

**Project:** The Democratization Safety Paradox: Multilingual Safety Collapse in Small Language Models  
**Requested:** $350 USD  
**Duration:** ~1 month (active compute phases)

---

## Budget Breakdown

| Item | Purpose | Cost |
|------|---------|------|
| Claude Code Max (1 month) | Development environment, code assistance, orchestration | $200 |
| RunPod GPU compute | Cloud inference for 12B + 27B models (RTX 4090) | $50 |
| Anthropic API (Claude Haiku) | LLM-as-judge for 2,400+ model responses | $20 |
| Contingency | Reruns, debugging, unexpected compute needs | $80 |
| **Total** | | **$350** |

---

## Detailed Compute Estimates

### RunPod GPU (RTX 4090 @ ~$0.74/hr)

| Task | Model | Est. hours | Cost |
|------|-------|-----------|------|
| Inference runs | Gemma 4 12B | 4 h | $3 |
| Inference runs | Gemma 4 27B | 9 h | $7 |
| Activation extraction (mechanistic analysis) | 12B + 27B | 11 h | $8 |
| Debugging + reruns buffer | — | 10 h | $7 |
| **Subtotal** | | **34 h** | **$25** |

> Padded to $50 to account for unexpected reruns and pod startup/teardown overhead.

### Anthropic API (Claude Haiku, claude-haiku-4-5-20251001)

| Task | Volume | Est. tokens | Cost |
|------|--------|------------|------|
| LLM judging (4 model sizes × 6 languages × 50 prompts × 2 conditions) | 2,400 calls | ~1.2M input + 24K output | ~$2 |
| Buffer for retries + validation | — | — | $3 |
| **Subtotal** | | | **$5** |

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
- **12B + 27B require cloud** — exceed laptop VRAM. RunPod is ~4x cheaper than AWS equivalent.
- **Haiku for judging, not GPT-4** — Wang et al. used GPT-4 for evaluation. We use Claude Haiku (equivalent quality, $0.25/MTok vs $15/MTok). This reduces API cost by ~60x.
- **No dataset cost** — WildGuardMix is publicly available on HuggingFace. Free.
- **No HuggingFace cost** — model weights are free (gated but no charge). Dataset hosting on HuggingFace is free.

---

## Cost if Funds Not Available

Phases 0–3 can be completed with **$0** (local compute only). Phases 4–7 require ~$30–50 for cloud GPU. The full $350 request includes Claude Code Max, which is the primary value multiplier for the research workflow.

Minimum viable budget (cloud only, no Claude Code): ~$50.
