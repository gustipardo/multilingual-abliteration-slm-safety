"""
Phase 5: Compute Silhouette Scores for harmful/harmless cluster separation.
Replicates Wang et al. (2505.17306) Table 1 for Gemma 4 variants.

Usage:
    python scripts/05_silhouette_scores.py --size e2b
    python scripts/05_silhouette_scores.py --all

Output: data/outputs/silhouette_scores.csv
        figures/pca_{size}_{lang}.png
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


def load_config():
    with open("configs/experiment.yaml") as f:
        return yaml.safe_load(f)


def load_model(model_id, hw_cfg):
    quant_config = None
    if hw_cfg["load_in_4bit"]:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16
        )
    elif hw_cfg["load_in_8bit"]:
        quant_config = BitsAndBytesConfig(load_in_8bit=True)

    dtype = torch.bfloat16 if hw_cfg["dtype"] == "bfloat16" else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=quant_config,
        torch_dtype=dtype if quant_config is None else None,
        device_map=hw_cfg["device_map"],
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    return model, tokenizer


def get_activations(model, tokenizer, texts, layer_idx):
    activations = []
    for text in tqdm(texts, leave=False):
        inputs = tokenizer(text, return_tensors="pt",
                           truncation=True, max_length=512).to(model.device)
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)
        hidden = outputs.hidden_states[layer_idx][0, -1, :].float().cpu()
        activations.append(hidden.numpy())
    return np.array(activations)


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
                 f"PC1: {pca.explained_variance_ratio_[0]*100:.1f}% | "
                 f"PC2: {pca.explained_variance_ratio_[1]*100:.1f}%", fontsize=11)
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

    model, tokenizer = load_model(model_id, hw_cfg)
    out_dir = Path("figures")
    out_dir.mkdir(exist_ok=True)
    results = []

    harmless_pool = [
        "Tell me a fun fact about space.",
        "What is the capital of Germany?",
        "How does a rainbow form?",
        "Recommend a book for beginners in cooking.",
        "Explain the rules of chess.",
    ]

    for lang in cfg["languages"]:
        prompt_file = Path(f"data/prompts/{lang}.jsonl")
        if not prompt_file.exists():
            print(f"  Skipping {lang} — prompt file missing")
            continue

        with open(prompt_file) as f:
            prompts = [json.loads(line) for line in f]

        prompt_key = f"prompt_{lang}" if lang != "en" else "prompt_en"
        harmful_texts = [p.get(prompt_key, p["prompt_en"]) for p in prompts]
        harmless_texts = (harmless_pool * (len(harmful_texts) // 5 + 1))[:len(harmful_texts)]

        print(f"  Computing Silhouette Score: {size} × {lang}...")
        harmful_acts = get_activations(model, tokenizer, harmful_texts, layer_idx)
        harmless_acts = get_activations(model, tokenizer, harmless_texts, layer_idx)

        X = np.concatenate([harmful_acts, harmless_acts])
        labels = [0] * len(harmful_acts) + [1] * len(harmless_acts)
        score = silhouette_score(X, labels)

        fig_path = plot_pca(harmful_acts, harmless_acts, lang, size, out_dir)
        print(f"    Score: {score:.4f} | PCA → {fig_path}")

        results.append({"size": size, "language": lang, "silhouette_score": score})

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", choices=["e2b", "e4b", "12b", "27b"])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    sizes = ["e2b", "e4b", "12b", "27b"] if args.all else [args.size]
    all_results = []

    for size in sizes:
        print(f"\n=== {size.upper()} ===")
        all_results.extend(compute_size(size))

    df = pd.DataFrame(all_results)
    out_path = Path("data/outputs/silhouette_scores.csv")
    df.to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")

    # Summary pivot
    pivot = df.pivot(index="size", columns="language", values="silhouette_score")
    print("\nSilhouette Scores by model size × language:")
    print(pivot.round(4).to_string())

    # Heatmap
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
