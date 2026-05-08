"""
Phase 2b: Build the harmless prompt pool used as the contrast set for refusal
direction extraction (Wang et al. 2025 methodology). Mirrors the schema of
01_prepare_dataset.py so scripts 04/05 can use the same `prompt_{lang}` lookup.

Why a separate harmless dataset:
- Refusal direction = mean(harmful_acts) - mean(harmless_acts), normalized.
- If harmless prompts are in English while harmful prompts are in target lang X,
  the resulting direction conflates "harmful vs harmless" with "English vs X".
- Each language must have its own harmless prompts.

Usage:
    python scripts/01b_prepare_harmless.py
    python scripts/01b_prepare_harmless.py --translate-with claude   # higher quality

Output: data/prompts/harmless.jsonl
"""

import json
import argparse
from pathlib import Path

import yaml
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Curated benign prompts. Domain-diverse so the resulting "harmless cluster"
# spans general knowledge rather than a single topic.
HARMLESS_EN = [
    "Tell me an interesting fact about science.",
    "What is the capital of France?",
    "Explain how photosynthesis works.",
    "What are some popular tourist destinations?",
    "How do I make a cup of tea?",
    "Recommend a book for beginners learning to cook.",
    "Describe how a rainbow forms.",
    "What are the rules of chess?",
    "How does a bicycle stay upright while moving?",
    "Suggest a few stretches I can do at my desk.",
]


GOOGLE_LANG_MAP = {
    "zh": "zh-CN",
    "pt": "pt",
    "ar": "ar",
    "hi": "hi",
    "es": "es",
    "de": "de",
}


def load_config():
    with open("configs/experiment.yaml") as f:
        return yaml.safe_load(f)


def translate_google(prompts, target_lang):
    from deep_translator import GoogleTranslator
    google_code = GOOGLE_LANG_MAP.get(target_lang, target_lang)
    translator = GoogleTranslator(source="en", target=google_code)
    out = []
    for p in tqdm(prompts, desc=f"Translating → {target_lang}"):
        try:
            out.append(translator.translate(p))
        except Exception as e:
            print(f"  Translation failed, keeping English: {e}")
            out.append(p)
    return out


def translate_claude(prompts, target_lang):
    import anthropic
    client = anthropic.Anthropic()
    lang_names = {"es": "Spanish", "zh": "Simplified Chinese",
                  "ar": "Arabic", "hi": "Hindi", "pt": "Portuguese",
                  "de": "German"}
    out = []
    for p in tqdm(prompts, desc=f"Translating → {target_lang} (Claude)"):
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content":
                f"Translate this text to {lang_names[target_lang]}. "
                f"Return ONLY the translation, no explanation.\n\nText: {p}"}]
        )
        out.append(msg.content[0].text.strip())
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--translate-with", choices=["google", "claude"],
                        default="google")
    args = parser.parse_args()

    cfg = load_config()
    languages = cfg["languages"]
    out_path = Path("data/prompts/harmless.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [{"id": f"h{i:03d}", "prompt_en": p, "category": "harmless"}
            for i, p in enumerate(HARMLESS_EN)]

    for lang in languages:
        if lang == "en":
            continue
        translated = (translate_claude(HARMLESS_EN, lang)
                      if args.translate_with == "claude"
                      else translate_google(HARMLESS_EN, lang))
        for row, t in zip(rows, translated):
            row[f"prompt_{lang}"] = t

    with open(out_path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(rows)} harmless prompts × {len(languages)} languages → {out_path}")
    print("Schema matches data/prompts/{lang}.jsonl — scripts 04 and 05 can read directly.")


if __name__ == "__main__":
    main()
