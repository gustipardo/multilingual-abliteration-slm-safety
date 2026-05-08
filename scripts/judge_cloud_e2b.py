"""One-off: judge the 12 cloud jsonls in data/_runpod_e2b_2026-05-08/ via Anthropic API.
Reuses judge_file() from 03_llm_judge.py. Writes *_judged.jsonl alongside, no contamination
of data/outputs/.
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("judge_mod", Path(__file__).parent / "03_llm_judge.py")
judge_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge_mod)

import anthropic

cfg = judge_mod.load_config()
client = anthropic.Anthropic()
judge_model = cfg["evaluation"]["judge_model"]

cloud_dir = Path("data/_runpod_e2b_2026-05-08")
files = sorted(p for p in cloud_dir.glob("*.jsonl")
               if "_judged" not in p.name and not p.name.endswith(".partial.jsonl"))

print(f"Judging {len(files)} cloud files with {judge_model}\n")
for i, f in enumerate(files, 1):
    print(f"── file {i}/{len(files)}: {f.name} ──")
    judge_mod.judge_file(client, f, judge_model)
print("\n✓ done")
