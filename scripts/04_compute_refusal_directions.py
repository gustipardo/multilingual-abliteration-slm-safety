"""
Phase 5: Extract refusal directions and compute cross-lingual cosine similarity.
Replicates Wang et al. (2505.17306) mechanistic analysis for Gemma 4 variants.

Usage:
    python scripts/04_compute_refusal_directions.py --size e2b
    python scripts/04_compute_refusal_directions.py --size e4b

Output: data/outputs/refusal_directions_{size}.pt  (dict of {lang: direction_tensor})
        data/outputs/cosine_similarity_{size}.csv
"""

import json
import argparse
from pathlib import Path

import torch
import numpy as np
import pandas as pd
import yaml
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
        output_hidden_states=True,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    return model, tokenizer


def get_last_token_activations(model, tokenizer, texts, layer_idx):
    """Extract residual stream activation at last token position, specific layer."""
    activations = []

    for text in tqdm(texts, desc="Extracting activations", leave=False):
        inputs = tokenizer(text, return_tensors="pt",
                           truncation=True, max_length=512).to(model.device)
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)

        # hidden_states[layer_idx] shape: (1, seq_len, hidden_dim)
        hidden = outputs.hidden_states[layer_idx]
        last_token = hidden[0, -1, :].float().cpu()
        activations.append(last_token)

    return torch.stack(activations)  # (n_prompts, hidden_dim)


def compute_refusal_direction(harmful_acts, harmless_acts):
    """Mean difference direction, normalized."""
    direction = harmful_acts.mean(0) - harmless_acts.mean(0)
    return direction / direction.norm()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", required=True, choices=["e2b", "e4b", "12b", "27b"])
    args = parser.parse_args()

    cfg = load_config()
    torch.manual_seed(cfg["seed"])
    layer_idx = cfg["mechanistic"]["layer_idx"]

    # Use BASE model for refusal direction extraction
    model_id = cfg["models"]["base"][args.size]
    hw_cfg = cfg["hardware"][args.size]
    model, tokenizer = load_model(model_id, hw_cfg)

    out_dir = Path("data/outputs")
    out_dir.mkdir(exist_ok=True)

    refusal_dirs = {}

    for lang in cfg["languages"]:
        prompt_file = Path(f"data/prompts/{lang}.jsonl")
        if not prompt_file.exists():
            print(f"Skipping {lang} — prompt file missing")
            continue

        with open(prompt_file) as f:
            prompts = [json.loads(line) for line in f]

        prompt_key = f"prompt_{lang}" if lang != "en" else "prompt_en"
        harmful_texts = [p.get(prompt_key, p["prompt_en"]) for p in prompts]

        # Harmless: replace harmful request with benign version
        # Simple approach: use the English "What is the weather today?" as harmless
        # Better: use WildGuardMix's benign prompts
        harmless_texts = [
            "Tell me an interesting fact about science.",
            "What is the capital of France?",
            "Explain how photosynthesis works.",
            "What are some popular tourist destinations?",
            "How do I make a cup of tea?",
        ] * (len(harmful_texts) // 5 + 1)
        harmless_texts = harmless_texts[:len(harmful_texts)]

        print(f"\nExtracting activations for {lang} ({args.size})...")
        harmful_acts = get_last_token_activations(model, tokenizer, harmful_texts, layer_idx)
        harmless_acts = get_last_token_activations(model, tokenizer, harmless_texts, layer_idx)

        direction = compute_refusal_direction(harmful_acts, harmless_acts)
        refusal_dirs[lang] = direction
        print(f"  Refusal direction shape: {direction.shape}")

    # Save directions
    torch.save(refusal_dirs, out_dir / f"refusal_directions_{args.size}.pt")
    print(f"\nSaved refusal directions → data/outputs/refusal_directions_{args.size}.pt")

    # Cross-lingual cosine similarity matrix
    languages = list(refusal_dirs.keys())
    n = len(languages)
    sim_matrix = np.zeros((n, n))

    for i, l1 in enumerate(languages):
        for j, l2 in enumerate(languages):
            sim = torch.nn.functional.cosine_similarity(
                refusal_dirs[l1].unsqueeze(0),
                refusal_dirs[l2].unsqueeze(0)
            ).item()
            sim_matrix[i, j] = sim

    df_sim = pd.DataFrame(sim_matrix, index=languages, columns=languages)
    sim_path = out_dir / f"cosine_similarity_{args.size}.csv"
    df_sim.to_csv(sim_path)
    print(f"Saved cosine similarity matrix → {sim_path}")
    print(f"\nCross-lingual refusal direction cosine similarity ({args.size}):")
    print(df_sim.round(3).to_string())


if __name__ == "__main__":
    main()
