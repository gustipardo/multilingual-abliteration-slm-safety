"""Compare cloud E2B compliance (12 cells from data/_runpod_e2b_2026-05-08/_judged) against
the archived local E2B baseline (data/_archive_local_e2b_2026-05-07/).

Prints per-cell delta and a summary. The 2 missing cells (ar/hi abliterated) are noted.
"""
import json, csv
from pathlib import Path

ARCHIVE_LOCAL = Path("data/_archive_local_e2b_2026-05-07/compliance_rates_e2b_only.csv")
CLOUD_DIR = Path("data/_runpod_e2b_2026-05-08")

# Load local baseline: dict[(condition, lang)] -> compliance
local = {}
with open(ARCHIVE_LOCAL) as f:
    for row in csv.DictReader(f):
        local[(row["condition"], row["language"])] = float(row["compliance_rate"])

# Compute cloud compliance from _judged.jsonl files in CLOUD_DIR
cloud = {}
for jp in sorted(CLOUD_DIR.glob("e2b_*_judged.jsonl")):
    parts = jp.stem.replace("_judged", "").split("_")
    # e2b_base_en  ->  ['e2b', 'base', 'en']
    cond, lang = parts[1], parts[2]
    rows = [json.loads(l) for l in open(jp)]
    n_complied = sum(r["complied"] for r in rows)
    cloud[(cond, lang)] = n_complied / len(rows)

# Per-cell diff
LANGS = ["en", "es", "zh", "pt", "de", "ar", "hi"]
print(f"\n{'cell':<22} {'local':>8} {'cloud':>8} {'Δ':>8}")
print("─" * 50)

for cond in ["base", "abliterated"]:
    for lang in LANGS:
        key = (cond, lang)
        if key not in cloud:
            print(f"{cond:<11} {lang:<10} {local.get(key, 0):>8.3f} {'(missing)':>8} {'':>8}")
            continue
        delta = cloud[key] - local[key]
        flag = "  ⚠" if abs(delta) > 0.05 else ""
        print(f"{cond:<11} {lang:<10} {local[key]:>8.3f} {cloud[key]:>8.3f} {delta:>+8.3f}{flag}")

# Summary means (only on cells we have in both)
common = set(local) & set(cloud)
local_mean = sum(local[k] for k in common) / len(common)
cloud_mean = sum(cloud[k] for k in common) / len(common)
print(f"\n{'mean over '+str(len(common))+' shared cells':<22} {local_mean:>8.3f} {cloud_mean:>8.3f} {cloud_mean-local_mean:>+8.3f}")

# Per-condition means on shared cells
for cond in ["base", "abliterated"]:
    cells = [(c, l) for (c, l) in common if c == cond]
    if not cells:
        continue
    lm = sum(local[k] for k in cells) / len(cells)
    cm = sum(cloud[k] for k in cells) / len(cells)
    print(f"{'mean '+cond+' ('+str(len(cells))+' cells)':<22} {lm:>8.3f} {cm:>8.3f} {cm-lm:>+8.3f}")

print(f"\nMissing from cloud: ar/hi abliterated (Pod 3 died before reaching them).")
print(f"Local baseline values for those:  ar abl = {local[('abliterated','ar')]:.3f}, hi abl = {local[('abliterated','hi')]:.3f}")
