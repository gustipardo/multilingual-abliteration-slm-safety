"""
Preflight check: verifies the .env file has every credential the pipeline needs.
Exits with non-zero status if anything is missing, so shell wrappers can `set -e`.

Usage:
    python scripts/00_check_env.py            # full check
    python scripts/00_check_env.py --inference-only   # skip ANTHROPIC_API_KEY
"""

import argparse
import os
import sys

from dotenv import load_dotenv

REQUIRED_FOR_INFERENCE = {
    "HUGGINGFACE_TOKEN": "Required to download Gemma 4 (gated). Accept license at "
                         "https://huggingface.co/google/gemma-4-e2b-it",
}
REQUIRED_FOR_JUDGING = {
    "ANTHROPIC_API_KEY": "Required for Claude Haiku as LLM-as-judge. Get one at "
                         "https://console.anthropic.com",
}
OPTIONAL = {
    "RUNPOD_API_KEY": "Only needed when launching cloud GPU pods for 26B/31B.",
}


def check(keys, severity, problems, notes):
    for key, hint in keys.items():
        val = os.getenv(key)
        if not val or val.endswith("..."):
            problems.append((severity, key, hint))
        else:
            notes.append(f"  {severity} {key} OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inference-only", action="store_true",
                        help="Only check inference-time credentials (skip judge key)")
    args = parser.parse_args()

    load_dotenv()
    problems = []
    notes = []

    check(REQUIRED_FOR_INFERENCE, "[required]", problems, notes)
    if not args.inference_only:
        check(REQUIRED_FOR_JUDGING, "[required]", problems, notes)
    for key, hint in OPTIONAL.items():
        if not os.getenv(key) or os.getenv(key, "").endswith("..."):
            notes.append(f"  [optional] {key} unset — {hint}")
        else:
            notes.append(f"  [optional] {key} OK")

    if notes:
        print("Environment check:")
        for n in notes:
            print(n)

    if problems:
        print("\nMissing credentials:")
        for severity, key, hint in problems:
            print(f"  {severity} {key}: {hint}")
        print("\nAdd them to .env (see .env.example).")
        sys.exit(1)

    print("\nAll required credentials present.")


if __name__ == "__main__":
    main()
