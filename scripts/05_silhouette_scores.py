"""
Phase 5: Compute Silhouette Scores for harmful/harmless cluster separation.
Replicates Wang et al. (2505.17306) Table 1 for Gemma 4 variants.

Methodology notes (same as 04_compute_refusal_directions.py):
- Harmless prompts must be in the SAME language as the harmful set, otherwise
  the cluster separation conflates language identity with harm.
- Activations extracted AFTER applying the model's chat template, matching
  the runtime prompt format used in script 02.

Usage:
    python scripts/05_silhouette_scores.py --size e2b
    python scripts/05_silhouette_scores.py --all                 # local sizes only
    python scripts/05_silhouette_scores.py --all --force          # bypass VRAM guard

Output: data/outputs/silhouette_scores.csv
        figures/pca_{size}_{lang}.png
        figures/silhouette_heatmap.png
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import pandas as pd
import yaml
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from tqdm import tqdm

# Sizes that fit on a typical laptop GPU (~8GB) at 4-bit. 26B/31B require
# RunPod or similar. Override with --force.
LOCAL_SIZES = {"e2b", "e4b"}


def load_config():
    with open("configs/experiment.yaml") as f:
        return yaml.safe_load(f)


def load_model(model_id, hw_cfg):
    quant_config = None
    if hw_cfg["load_in_4bit"]:
        # Same config as scripts/02_run_inference.py and scripts/04_*. Keeping
        # double_quant aligned across all three stages avoids tiny numerical
        # drift between the model that produced the responses and the one
        # whose activations we analyze.
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
    elif hw_cfg["load_in_8bit"]:
        quant_config = BitsAndBytesConfig(load_in_8bit=True)

    dtype = torch.bfloat16 if hw_cfg["dtype"] == "bfloat16" else torch.float16
    if quant_config is not None and torch.cuda.is_available():
        device_map = {"": 0}
    else:
        device_map = hw_cfg["device_map"]

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=quant_config,
        dtype=dtype if quant_config is None else None,
        device_map=device_map,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    return model, tokenizer


def format_with_chat_template(tokenizer, text):
    if tokenizer.chat_template:
        return tokenizer.apply_chat_template(
            [{"role": "user", "content": text}],
            tokenize=False, add_generation_prompt=True,
        )
    return text


def get_activations(model, tokenizer, texts, layer_idx):
    activations = []
    for text in tqdm(texts, leave=False):
        formatted = format_with_chat_template(tokenizer, text)
        inputs = tokenizer(formatted, return_tensors="pt",
                           truncation=True, max_length=512).to(model.device)
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)
        hidden = outputs.hidden_states[layer_idx][0, -1, :].float().cpu()
        activations.append(hidden.numpy())
    return np.array(activations)


def load_prompts_for_lang(prompt_file, lang):
    if not prompt_file.exists():
        return None
    with open(prompt_file) as f:
        prompts = [json.loads(line) for line in f]
    key = f"prompt_{lang}"
    return [p.get(key, p["prompt_en"]) for p in prompts]


def plot_pca(harmful_acts, harmless_acts, lang, size, out_dir):
    pca = PCA(n_components=2)
    X = np.concatenate([harmful_acts, harmless_acts])
    X_2d = pca.fit_transform(X)
    n = len(harmful_acts)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(X_2d[:n, 0], X_2d[:n, 1], c="#e74c3c", alpha=0.6,
               s=40, label="harmful", zorder=3)
    ax.scatter(X_2d[n:, 0], X_2d[n:, 1], c="#3498db", alpha=0.6,
               s=40, label="harmless", zorder=3)
    ax.set_title(f"Gemma 4 {size.upper()} — {lang.upper()}\n"
                 f"PC1: {pca.explained_variance_ratio_[0] * 100:.1f}% | "
                 f"PC2: {pca.explained_variance_ratio_[1] * 100:.1f}%", fontsize=11)
    ax.legend(fontsize=9)
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    plt.tight_layout()
    out_path = out_dir / f"pca_{size}_{lang}.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def compute_size(size):
    cfg = load_config()
    layer_idx = cfg["mechanistic"]["layer_idx"]
    model_id = cfg["models"]["base"][size]
    hw_cfg = cfg["hardware"][size]

    harmless_path = Path("data/prompts/harmless.jsonl")
    if not harmless_path.exists():
        raise SystemExit(
            f"{harmless_path} missing. Run scripts/01b_prepare_harmless.py first."
        )

    print(f"Loading {model_id}...")
    model, tokenizer = load_model(model_id, hw_cfg)
    fig_dir = Path("figures")
    fig_dir.mkdir(parents=True, exist_ok=True)
    results = []

    for lang in cfg["languages"]:
        harmful_texts = load_prompts_for_lang(Path(f"data/prompts/{lang}.jsonl"), lang)
        if harmful_texts is None:
            print(f"  Skipping {lang} — harmful prompt file missing")
            continue
        harmless_texts = load_prompts_for_lang(harmless_path, lang)

        print(f"  [{size}/{lang}] {len(harmful_texts)} harmful + "
              f"{len(harmless_texts)} harmless")
        harmful_acts = get_activations(model, tokenizer, harmful_texts, layer_idx)
        harmless_acts = get_activations(model, tokenizer, harmless_texts, layer_idx)

        X = np.concatenate([harmful_acts, harmless_acts])
        labels = [0] * len(harmful_acts) + [1] * len(harmless_acts)
        score = silhouette_score(X, labels)

        fig_path = plot_pca(harmful_acts, harmless_acts, lang, size, fig_dir)
        print(f"    Silhouette={score:.4f} | PCA → {fig_path}")
        results.append({"size": size, "language": lang, "silhouette_score": score})

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=["e2b", "e4b", "26b", "31b"])
    parser.add_argument("--all", action="store_true",
                        help="Run all sizes that fit locally (use --force to include 26b/31b)")
    parser.add_argument("--force", action="store_true",
                        help="Bypass the local-size guard (intended for RunPod)")
    args = parser.parse_args()

    if args.all:
        sizes = ["e2b", "e4b", "26b", "31b"]
        if not args.force:
            sizes = [s for s in sizes if s in LOCAL_SIZES]
            print(f"Local mode: running {sizes}. Use --force to include cloud sizes.")
    elif args.size:
        if args.size not in LOCAL_SIZES and not args.force:
            print(f"Warning: {args.size} typically requires RunPod. Use --force to run anyway.")
            return
        sizes = [args.size]
    else:
        parser.error("Provide --size or --all")

    all_results = []
    for size in sizes:
        print(f"\n=== {size.upper()} ===")
        all_results.extend(compute_size(size))

    if not all_results:
        return

    df = pd.DataFrame(all_results)
    out_path = Path("data/outputs/silhouette_scores.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Merge with existing scores from previous size runs (idempotent across sizes)
    if out_path.exists():
        prior = pd.read_csv(out_path)
        df = pd.concat([prior[~prior["size"].isin(df["size"].unique())], df],
                       ignore_index=True)

    df.to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")

    pivot = df.pivot(index="size", columns="language", values="silhouette_score")
    print("\nSilhouette Scores by model size × language:")
    print(pivot.round(4).to_string())

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(pivot.astype(float), annot=True, fmt=".3f",
                cmap="RdYlGn", vmin=-0.1, vmax=0.5, ax=ax)
    ax.set_title("Silhouette Scores: Harmful/Harmless Cluster Separation\n"
                 "(Higher = better separation = harder to abliterate)")
    plt.tight_layout()
    fig_path = Path("figures/silhouette_heatmap.png")
    plt.savefig(fig_path, dpi=150)
    plt.close()
    print(f"Saved heatmap → {fig_path}")


if __name__ == "__main__":
    main()
