"""
Phase 5: Extract refusal directions and compute cross-lingual cosine similarity.
Replicates Wang et al. (2505.17306) mechanistic analysis for Gemma 4 variants.

Methodology notes:
- For each language X, harmful AND harmless prompts must both be in X.
  Harmful prompts: data/prompts/{lang}.jsonl (BeaverTails sample, translated).
  Harmless prompts: data/prompts/harmless.jsonl (built by 01b_prepare_harmless.py).
  Otherwise the resulting direction conflates "harmful vs harmless" with
  "English vs target language".
- Activations are extracted AFTER applying the model's chat template, matching
  how the model is actually run during inference (script 02). This is also the
  convention used by Arditi et al. (2024) and Wang et al. (2025).

Usage:
    python scripts/04_compute_refusal_directions.py --size e2b
    python scripts/04_compute_refusal_directions.py --size e4b

Output: data/outputs/refusal_directions_{size}.pt   (dict {lang: tensor})
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
        # Same config as scripts/02_run_inference.py — keep aligned so the
        # mechanistic activations come from the *exact* same loaded weights
        # as the inference responses. Double-quant is the load-time default we
        # use for compliance runs; mismatching it here would introduce a tiny
        # numerical drift between the two stages.
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


def get_last_token_activations(model, tokenizer, texts, layer_idx):
    activations = []
    for text in tqdm(texts, desc="Activations", leave=False):
        formatted = format_with_chat_template(tokenizer, text)
        inputs = tokenizer(formatted, return_tensors="pt",
                           truncation=True, max_length=512).to(model.device)
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True)
        hidden = outputs.hidden_states[layer_idx]    # (1, seq_len, hidden_dim)
        activations.append(hidden[0, -1, :].float().cpu())
    return torch.stack(activations)                  # (n_prompts, hidden_dim)


def load_prompts_for_lang(prompt_file, lang):
    if not prompt_file.exists():
        return None
    with open(prompt_file) as f:
        prompts = [json.loads(line) for line in f]
    key = f"prompt_{lang}"
    return [p.get(key, p["prompt_en"]) for p in prompts]


def compute_refusal_direction(harmful_acts, harmless_acts):
    direction = harmful_acts.mean(0) - harmless_acts.mean(0)
    return direction / direction.norm()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", required=True, choices=["e2b", "e4b", "26b", "31b"])
    args = parser.parse_args()

    cfg = load_config()
    torch.manual_seed(cfg["seed"])
    layer_idx = cfg["mechanistic"]["layer_idx"]

    # Refusal direction is computed on the BASE model (the one whose safety
    # geometry we want to characterize before abliteration disrupts it).
    model_id = cfg["models"]["base"][args.size]
    hw_cfg = cfg["hardware"][args.size]

    harmless_path = Path("data/prompts/harmless.jsonl")
    if not harmless_path.exists():
        raise SystemExit(
            f"{harmless_path} missing. Run scripts/01b_prepare_harmless.py first."
        )

    print(f"Loading {model_id}...")
    model, tokenizer = load_model(model_id, hw_cfg)

    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    refusal_dirs = {}
    for lang in cfg["languages"]:
        harmful_texts = load_prompts_for_lang(Path(f"data/prompts/{lang}.jsonl"), lang)
        if harmful_texts is None:
            print(f"  Skipping {lang} — harmful prompt file missing")
            continue
        harmless_texts = load_prompts_for_lang(harmless_path, lang)

        print(f"\n[{args.size}/{lang}] {len(harmful_texts)} harmful + "
              f"{len(harmless_texts)} harmless prompts")
        harmful_acts = get_last_token_activations(model, tokenizer, harmful_texts, layer_idx)
        harmless_acts = get_last_token_activations(model, tokenizer, harmless_texts, layer_idx)

        refusal_dirs[lang] = compute_refusal_direction(harmful_acts, harmless_acts)
        print(f"  refusal direction: shape={tuple(refusal_dirs[lang].shape)}")

    torch.save(refusal_dirs, out_dir / f"refusal_directions_{args.size}.pt")
    print(f"\nSaved → data/outputs/refusal_directions_{args.size}.pt")

    languages = list(refusal_dirs.keys())
    n = len(languages)
    sim_matrix = np.zeros((n, n))
    for i, l1 in enumerate(languages):
        for j, l2 in enumerate(languages):
            sim_matrix[i, j] = torch.nn.functional.cosine_similarity(
                refusal_dirs[l1].unsqueeze(0),
                refusal_dirs[l2].unsqueeze(0),
            ).item()

    df_sim = pd.DataFrame(sim_matrix, index=languages, columns=languages)
    sim_path = out_dir / f"cosine_similarity_{args.size}.csv"
    df_sim.to_csv(sim_path)
    print(f"Saved → {sim_path}")
    print(f"\nCross-lingual refusal direction cosine similarity ({args.size}):")
    print(df_sim.round(3).to_string())


if __name__ == "__main__":
    main()
