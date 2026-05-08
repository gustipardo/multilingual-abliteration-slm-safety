"""
Phase 3/4: Run inference on base and abliterated Gemma 4 models.
Saves model responses to data/outputs/{size}_{condition}_{lang}.jsonl

Usage:
    # Local (E2B, E4B):
    python scripts/02_run_inference.py --size e2b --condition base
    python scripts/02_run_inference.py --size e2b --condition abliterated
    python scripts/02_run_inference.py --size e4b --condition abliterated

    # Sanity check (5 prompts, English only):
    python scripts/02_run_inference.py --size e4b --condition abliterated --sanity

    # All languages for one model:
    python scripts/02_run_inference.py --size e2b --condition abliterated --all-langs
"""

import json
import argparse
from pathlib import Path

import torch
import yaml
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from tqdm import tqdm


def load_config():
    with open("configs/experiment.yaml") as f:
        return yaml.safe_load(f)


def load_model(model_id, hw_cfg):
    print(f"Loading model: {model_id}")

    quant_config = None
    if hw_cfg["load_in_4bit"]:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
    elif hw_cfg["load_in_8bit"]:
        quant_config = BitsAndBytesConfig(load_in_8bit=True)

    dtype = torch.bfloat16 if hw_cfg["dtype"] == "bfloat16" else torch.float16

    # With bitsandbytes quantization, device_map="auto" over-estimates memory
    # and may allocate to CPU, which bnb doesn't allow. Force all to GPU 0.
    if quant_config is not None and torch.cuda.is_available():
        effective_device_map = {"": 0}
    else:
        effective_device_map = hw_cfg["device_map"]

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=quant_config,
        dtype=dtype if quant_config is None else None,
        device_map=effective_device_map,
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    return model, tokenizer


def run_inference(model, tokenizer, prompts, cfg, lang):
    inf_cfg = cfg["inference"]
    results = []

    for p in tqdm(prompts, desc=f"Inference [{lang}]"):
        prompt_key = f"prompt_{lang}"
        prompt_text = p.get(prompt_key, p["prompt_en"])  # fallback to EN if missing

        # Apply chat template if available
        if tokenizer.chat_template:
            messages = [{"role": "user", "content": prompt_text}]
            input_text = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        else:
            input_text = prompt_text

        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=inf_cfg["max_new_tokens"],
                do_sample=inf_cfg["do_sample"],
                pad_token_id=tokenizer.eos_token_id,
            )

        # Decode only generated tokens (not the prompt)
        generated = output_ids[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(generated, skip_special_tokens=True)

        results.append({
            "id": p["id"],
            "lang": lang,
            "prompt": prompt_text,
            "response": response,
            "category": p.get("category", "unknown"),
        })

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", required=True, choices=["e2b", "e4b", "26b", "31b"])
    parser.add_argument("--condition", required=True, choices=["base", "abliterated"])
    parser.add_argument("--lang", default=None, help="Single language (default: all)")
    parser.add_argument("--all-langs", action="store_true")
    parser.add_argument("--sanity", action="store_true",
                        help="Run 5 English prompts only — quick verification")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if the output file already exists")
    args = parser.parse_args()

    cfg = load_config()
    torch.manual_seed(cfg["seed"])

    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.sanity:
        langs = ["en"]
        n = 5
    elif args.lang:
        langs = [args.lang]
        n = None
    elif args.all_langs:
        langs = cfg["languages"]
        n = None
    else:
        langs = ["en"]
        n = None

    # Idempotency: filter out languages whose output already exists.
    # Sanity always runs (its purpose is verification), so it skips this filter.
    work = []
    for lang in langs:
        out_file = out_dir / f"{args.size}_{args.condition}_{lang}.jsonl"
        if out_file.exists() and not args.force and not args.sanity:
            print(f"  Skip {lang}: {out_file.name} exists (use --force to rerun)")
            continue
        work.append(lang)

    if not work:
        print("Nothing to do — all outputs already exist.")
        return

    model_id = cfg["models"][args.condition][args.size]
    hw_cfg = cfg["hardware"][args.size]
    model, tokenizer = load_model(model_id, hw_cfg)

    n_total = len(work)
    for i, lang in enumerate(work, 1):
        prompt_file = Path(f"data/prompts/{lang}.jsonl")
        if not prompt_file.exists():
            print(f"  Skipping {lang} — {prompt_file} not found. Run 01_prepare_dataset.py first.")
            continue

        with open(prompt_file) as f:
            prompts = [json.loads(line) for line in f]
        if n:
            prompts = prompts[:n]

        # Meta-progress between languages so a 7-language run shows where we are
        # without having to count tqdm bars.
        print(f"\n  ── language {i}/{n_total}: {lang.upper()} "
              f"({args.size}/{args.condition}) ──")

        results = run_inference(model, tokenizer, prompts, cfg, lang)

        out_file = out_dir / f"{args.size}_{args.condition}_{lang}.jsonl"
        with open(out_file, "w") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  ✓ saved {len(results)} responses → {out_file.name}")

    if args.sanity:
        print("\n=== SANITY CHECK — First 3 responses ===")
        out_file = out_dir / f"{args.size}_{args.condition}_en.jsonl"
        with open(out_file) as f:
            for i, line in enumerate(f):
                if i >= 3:
                    break
                r = json.loads(line)
                print(f"\n[{i+1}] Prompt: {r['prompt'][:80]}...")
                print(f"     Response: {r['response'][:200]}...")


if __name__ == "__main__":
    main()
