"""
Phase 2: Download WildGuardMix, sample 50 harmful prompts, translate to 6 languages.
Saves to data/prompts/{lang}.jsonl

Usage:
    python scripts/01_prepare_dataset.py
    python scripts/01_prepare_dataset.py --translate-with claude  # higher quality
"""

import json
import os
import random
import argparse
from pathlib import Path

import yaml
from dotenv import load_dotenv
from datasets import load_dataset
from tqdm import tqdm

load_dotenv()
# Pass token explicitly so gated datasets work
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")


def load_config():
    with open("configs/experiment.yaml") as f:
        return yaml.safe_load(f)


def sample_harmful_prompts(cfg):
    print(f"Downloading {cfg['dataset']['source']} from HuggingFace...")
    ds = load_dataset(cfg["dataset"]["source"], split=cfg["dataset"]["split"], token=HF_TOKEN)

    # BeaverTails: filter is_safe == False
    harm_filter = cfg["dataset"]["harm_filter"]
    harmful = ds.filter(lambda x: x[harm_filter] == False)  # noqa: E712
    print(f"Found {len(harmful)} harmful prompts in test set.")

    random.seed(cfg["seed"])
    indices = random.sample(range(len(harmful)), cfg["dataset"]["n_prompts"])
    sample = harmful.select(indices)

    def get_category(row):
        cat = row.get("category", {})
        if isinstance(cat, dict):
            active = [k for k, v in cat.items() if v]
            return active[0] if active else "unknown"
        return str(cat) if cat else "unknown"

    return [{"id": f"{i:03d}", "prompt_en": row["prompt"],
             "category": get_category(row)}
            for i, row in enumerate(sample)]


GOOGLE_LANG_MAP = {
    "zh": "zh-CN",  # deep_translator needs zh-CN not zh
    "pt": "pt",
    "ar": "ar",
    "hi": "hi",
    "es": "es",
}


def translate_google(prompts, target_lang):
    from deep_translator import GoogleTranslator
    google_code = GOOGLE_LANG_MAP.get(target_lang, target_lang)
    translator = GoogleTranslator(source="en", target=google_code)
    results = []
    for p in tqdm(prompts, desc=f"Translating → {target_lang}"):
        try:
            translated = translator.translate(p)
        except Exception as e:
            print(f"  Translation failed for prompt, keeping English: {e}")
            translated = p
        results.append(translated)
    return results


def translate_claude(prompts, target_lang):
    import anthropic
    from dotenv import load_dotenv
    load_dotenv()

    client = anthropic.Anthropic()
    lang_names = {"es": "Spanish", "zh": "Simplified Chinese",
                  "ar": "Arabic", "hi": "Hindi", "pt": "Portuguese"}

    results = []
    for p in tqdm(prompts, desc=f"Translating → {target_lang} (Claude)"):
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content":
                f"Translate this text to {lang_names[target_lang]}. "
                f"Return ONLY the translation, no explanation.\n\nText: {p}"}]
        )
        results.append(msg.content[0].text.strip())
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--translate-with", choices=["google", "claude"],
                        default="google", help="Translation backend")
    args = parser.parse_args()

    cfg = load_config()
    out_dir = Path("data/prompts")
    out_dir.mkdir(parents=True, exist_ok=True)

    prompts = sample_harmful_prompts(cfg)

    # Save English
    en_path = out_dir / "en.jsonl"
    with open(en_path, "w") as f:
        for p in prompts:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"Saved {len(prompts)} English prompts → {en_path}")

    # Translate and save other languages
    non_english = [l for l in cfg["languages"] if l != "en"]
    for lang in non_english:
        en_texts = [p["prompt_en"] for p in prompts]

        if args.translate_with == "claude":
            translated = translate_claude(en_texts, lang)
        else:
            translated = translate_google(en_texts, lang)

        lang_path = out_dir / f"{lang}.jsonl"
        with open(lang_path, "w") as f:
            for p, t in zip(prompts, translated):
                row = {**p, f"prompt_{lang}": t}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Saved {len(prompts)} prompts → {lang_path}")

    print("\nDone. Upload to HuggingFace for reproducibility:")
    print("  huggingface-cli upload YOUR_USERNAME/wildguard-multilingual-50 data/prompts/")


if __name__ == "__main__":
    main()
