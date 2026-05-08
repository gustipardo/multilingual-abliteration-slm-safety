"""
Unified pipeline runner: same command for any model size.

For the chosen size, it runs (idempotently — skips work already done):
  1. Env preflight check
  2. Inference: base × all 7 languages
  3. Inference: abliterated × all 7 languages
  4. Judging: every output not yet judged
  5. Mechanistic: refusal directions + silhouette score for this size
  6. Status: print the matrix

Usage:
    python scripts/run_pipeline.py --size e2b
    python scripts/run_pipeline.py --size e4b
    python scripts/run_pipeline.py --size 31b      # on RunPod
    # python scripts/run_pipeline.py --size 26b    # OUT OF SCOPE (MoE) — see FUTURE_WORK.md

    # Skip parts:
    python scripts/run_pipeline.py --size e2b --skip-judging
    python scripts/run_pipeline.py --size e2b --skip-mechanistic
    python scripts/run_pipeline.py --size e2b --inference-only

    # Force re-run cells that already have outputs:
    python scripts/run_pipeline.py --size e2b --force

The runner prints a banner with the run summary, numbered phase headers, and a
final timing table. A log file is written to logs/{size}_{YYYYMMDD_HHMMSS}.log
with one line per phase (start time, command, exit code, elapsed). The log
intentionally does NOT capture tqdm output so it stays grep-friendly; live
progress bars go to the terminal only.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Force line-buffered stdout so the banner and phase headers appear in real
# time even when stdout is piped to a file (otherwise Python block-buffers
# and subprocess output races ahead of the runner's own prints).
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent.parent
LOCAL_SIZES = {"e2b", "e4b"}
CLOUD_SIZES = {"26b", "31b"}

# Heuristic time budgets (minutes) for the banner.
# E2B numbers come from a measured run on RTX 4070 Laptop, 100×7×2 (2026-05-03):
#   base 94 min · abliterated 225 min · judging 27 min · mechanistic 2 min.
# (Abliterated takes ~2.4× base because compliant responses run to max_new_tokens
#  while base refuses early.) The other sizes are projected from this baseline.
# These are coarse — actual times depend on hardware and response length.
ESTIMATES_MIN = {
    # Local laptop (RTX 4070, 8GB) — matches measured E2B run
    "e2b": {"inference_base": 94, "inference_abl": 225, "judging": 27, "mechanistic": 2},
    # Local laptop, ~2× E2B (model is 2× larger, similar generation lengths)
    "e4b": {"inference_base": 190, "inference_abl": 450, "judging": 27, "mechanistic": 4},
    # RunPod RTX 5090 — bigger model offsets faster GPU
    "26b": {"inference_base": 180, "inference_abl": 360, "judging": 27, "mechanistic": 5},
    "31b": {"inference_base": 300, "inference_abl": 600, "judging": 27, "mechanistic": 10},
}

# ── ANSI helpers ───────────────────────────────────────────────────────────
# Colors on if TTY OR FORCE_COLOR is set; off if NO_COLOR is set.
USE_COLOR = (
    os.environ.get("NO_COLOR") is None
    and (sys.stdout.isatty() or os.environ.get("FORCE_COLOR") is not None)
)


def _c(code):
    return f"\033[{code}m" if USE_COLOR else ""


BOLD, DIM, RESET = _c("1"), _c("2"), _c("0")
CYAN, GREEN, YELLOW, RED, MAGENTA, BLUE = (
    _c("36"), _c("32"), _c("33"), _c("31"), _c("35"), _c("34"),
)


def term_width(default=78):
    try:
        return min(shutil.get_terminal_size().columns, 100)
    except Exception:
        return default


def hms(seconds):
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


# ── Logging ────────────────────────────────────────────────────────────────
class RunLog:
    """One-line-per-event structured log file. Independent of subprocess stdout."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(path, "w", buffering=1)  # line-buffered

    def event(self, kind: str, **fields):
        ts = datetime.now().isoformat(timespec="seconds")
        bits = [f"{k}={v}" for k, v in fields.items()]
        self.fh.write(f"{ts}  [{kind}] " + " ".join(bits) + "\n")

    def close(self):
        self.fh.close()


# ── Visual elements ────────────────────────────────────────────────────────
def banner(size, args, log_path, est_total_min, est_phases):
    w = term_width()
    title = f"  multilingual-abliteration · pipeline runner · size={size.upper()}  "
    pad = max(0, (w - len(title)) // 2)

    print()
    print(f"{BOLD}{CYAN}╔" + "═" * (w - 2) + f"╗{RESET}")
    print(f"{BOLD}{CYAN}║{RESET}{' ' * pad}{BOLD}{title}{RESET}{' ' * (w - 2 - pad - len(title))}{BOLD}{CYAN}║{RESET}")
    print(f"{BOLD}{CYAN}╚" + "═" * (w - 2) + f"╝{RESET}")
    print()

    rows = [
        ("Model size", f"{BOLD}{size}{RESET}  ({'cloud' if size in CLOUD_SIZES else 'local'})"),
        ("Languages", f"{BOLD}7{RESET}  · en es zh pt de ar hi"),
        ("Conditions", f"{BOLD}base + abliterated{RESET}"),
        ("Cells per condition", f"{BOLD}7 × 100 prompts = 700 inferences{RESET}"),
        ("Total cells this run", f"{BOLD}14{RESET}  (2 conditions × 7 langs)"),
        ("Quantization", "bnb 4-bit NF4 + DQ + bf16 compute"),
        ("Force rerun", f"{YELLOW}yes{RESET}" if args.force else "no (idempotent skip)"),
        ("Judging", "skipped" if args.skip_judging else "Claude Haiku"),
        ("Mechanistic", "skipped" if args.skip_mechanistic else "refusal dirs + silhouette + PCA"),
        ("Log file", f"{DIM}{log_path}{RESET}"),
        ("Started", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Estimated total", f"{BOLD}{MAGENTA}~{est_total_min} min ({hms(est_total_min * 60)}){RESET}"),
    ]
    label_w = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"  {DIM}{label.ljust(label_w)}{RESET}  {value}")

    print()
    print(f"  {DIM}phase plan:{RESET}")
    for i, (name, est) in enumerate(est_phases, 1):
        bar = f"~{est} min" if est else "~"
        print(f"    {DIM}[{i}/{len(est_phases)}]{RESET} {name}  {DIM}{bar}{RESET}")
    print()
    print(f"{DIM}" + "─" * w + f"{RESET}")
    print()


def phase_header(idx, total, name, cmd, est_min, log: RunLog):
    w = term_width()
    print()
    # Build the visible title (no ANSI inside the length calculation).
    plain_title = f" [{idx}/{total}] {name} "
    if est_min:
        plain_title += f"(~{est_min} min) "
    visible_len = len(plain_title)
    fill = max(0, w - visible_len - 4)  # 4 = "┌─" + "─┐"

    if est_min:
        styled_title = f" [{idx}/{total}] {name} {DIM}(~{est_min} min){RESET} "
    else:
        styled_title = plain_title

    print(f"{BOLD}{BLUE}┌─{styled_title}{'─' * fill}─┐{RESET}")
    print(f"  {DIM}$ {' '.join(cmd)}{RESET}")
    print(f"  {DIM}started {datetime.now().strftime('%H:%M:%S')}{RESET}")
    print()
    log.event("phase_start", n=idx, total=total, name=repr(name), cmd=" ".join(cmd))


def phase_footer(name, ok, elapsed, log: RunLog, exit_code=0):
    if ok:
        print()
        print(f"  {GREEN}✓{RESET} {name}  {DIM}done in {hms(elapsed)}{RESET}")
        log.event("phase_end", name=repr(name), status="ok", elapsed_s=int(elapsed))
    else:
        print()
        print(f"  {RED}✗ {name}  failed (exit {exit_code}) after {hms(elapsed)}{RESET}")
        log.event("phase_end", name=repr(name), status="fail",
                  exit_code=exit_code, elapsed_s=int(elapsed))


def final_summary(timings, total_elapsed, log_path, ok):
    w = term_width()
    print()
    print(f"{DIM}" + "─" * w + f"{RESET}")
    title = f"{GREEN}✓ Pipeline complete{RESET}" if ok else f"{RED}✗ Pipeline failed{RESET}"
    print(f"{BOLD}{title}{RESET}")
    print()

    label_w = max((len(name) for name, _, _ in timings), default=10)
    print(f"  {DIM}{'phase'.ljust(label_w)}   status   elapsed{RESET}")
    print(f"  {DIM}{'-' * label_w}   ------   -------{RESET}")
    for name, status, elapsed in timings:
        marker = f"{GREEN}✓{RESET}" if status == "ok" else (
            f"{YELLOW}-{RESET}" if status == "skip" else f"{RED}✗{RESET}")
        elapsed_str = hms(elapsed) if elapsed is not None else "—"
        print(f"  {name.ljust(label_w)}   {marker}        {elapsed_str}")
    print()
    print(f"  {BOLD}total elapsed:  {hms(total_elapsed)}{RESET}")
    print(f"  {DIM}log:            {log_path}{RESET}")
    print()


# ── Subprocess runner ──────────────────────────────────────────────────────
def run(cmd, label, idx, total, est_min, log: RunLog, timings):
    phase_header(idx, total, label, cmd, est_min, log)
    t0 = time.monotonic()
    result = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.monotonic() - t0
    if result.returncode == 0:
        phase_footer(label, True, elapsed, log)
        timings.append((label, "ok", elapsed))
        return True
    else:
        phase_footer(label, False, elapsed, log, exit_code=result.returncode)
        timings.append((label, "fail", elapsed))
        return False


def skip(label, reason, timings, log: RunLog):
    print()
    print(f"  {YELLOW}↷{RESET} {label}  {DIM}skipped — {reason}{RESET}")
    log.event("phase_skip", name=repr(label), reason=reason)
    timings.append((label, "skip", None))


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", required=True, choices=["e2b", "e4b", "26b", "31b"])
    parser.add_argument("--skip-judging", action="store_true")
    parser.add_argument("--skip-mechanistic", action="store_true")
    parser.add_argument("--inference-only", action="store_true",
                        help="Equivalent to --skip-judging --skip-mechanistic")
    parser.add_argument("--force", action="store_true",
                        help="Re-run cells whose outputs already exist")
    args = parser.parse_args()

    if args.inference_only:
        args.skip_judging = True
        args.skip_mechanistic = True

    py = sys.executable
    size = args.size

    # ── Plan phases (and time estimates) ────────────────────────────────
    est = ESTIMATES_MIN.get(size, ESTIMATES_MIN["e4b"])
    plan = [
        ("Env preflight", 0),
        ("Inference: base × 7 languages", est["inference_base"]),
        ("Inference: abliterated × 7 languages", est["inference_abl"]),
    ]
    if not args.skip_judging:
        plan.append(("Judging (Claude Haiku)", est["judging"]))
    if not args.skip_mechanistic:
        plan.append(("Refusal directions", max(1, est["mechanistic"] // 2)))
        plan.append(("Silhouette + PCA", max(1, est["mechanistic"] // 2)))
    plan.append(("Status snapshot", 0))
    est_total = sum(e for _, e in plan)

    # ── Set up log ──────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = ROOT / "logs" / f"{size}_{timestamp}.log"
    log = RunLog(log_path)
    log.event("run_start", size=size, force=args.force,
              skip_judging=args.skip_judging, skip_mechanistic=args.skip_mechanistic,
              estimated_min=est_total)

    banner(size, args, log_path.relative_to(ROOT), est_total, plan)

    timings = []
    t_start = time.monotonic()

    total = len(plan)
    idx = 1

    # 1. Env preflight
    env_cmd = [py, "scripts/00_check_env.py"]
    if args.skip_judging:
        env_cmd.append("--inference-only")
    if not run(env_cmd, plan[0][0], idx, total, plan[0][1], log, timings):
        log.close()
        final_summary(timings, time.monotonic() - t_start, log_path, ok=False)
        sys.exit(1)
    idx += 1

    # 1b. Data preparation (silent: no phase header, just a one-liner if needed)
    harmful_missing = not (ROOT / "data" / "prompts" / "en.jsonl").exists()
    if harmful_missing:
        print(f"  {DIM}preparing harmful prompt set (one-time)...{RESET}")
        subprocess.run([py, "scripts/01_prepare_dataset.py"], cwd=ROOT, check=True)
    if not args.skip_mechanistic:
        harmless_path = ROOT / "data" / "prompts" / "harmless.jsonl"
        if not harmless_path.exists():
            print(f"  {DIM}preparing harmless prompt set (one-time, Claude translation)...{RESET}")
            subprocess.run([py, "scripts/01b_prepare_harmless.py",
                            "--translate-with", "claude"], cwd=ROOT, check=True)

    # 2 & 3. Inference (base + abliterated)
    for cond_idx, cond in enumerate(("base", "abliterated")):
        cmd = [py, "scripts/02_run_inference.py",
               "--size", size, "--condition", cond, "--all-langs"]
        if args.force:
            cmd.append("--force")
        phase_name = plan[idx - 1][0]
        if not run(cmd, phase_name, idx, total, plan[idx - 1][1], log, timings):
            log.close()
            final_summary(timings, time.monotonic() - t_start, log_path, ok=False)
            sys.exit(1)
        idx += 1

    # 4. Judging
    if args.skip_judging:
        skip("Judging (Claude Haiku)", "--skip-judging", timings, log)
    else:
        cmd = [py, "scripts/03_llm_judge.py", "--all"]
        if not run(cmd, plan[idx - 1][0], idx, total, plan[idx - 1][1], log, timings):
            log.close()
            final_summary(timings, time.monotonic() - t_start, log_path, ok=False)
            sys.exit(1)
        idx += 1

    # 5. Mechanistic
    if args.skip_mechanistic:
        skip("Refusal directions", "--skip-mechanistic", timings, log)
        skip("Silhouette + PCA", "--skip-mechanistic", timings, log)
    else:
        # 5a. Refusal directions
        refusal_path = ROOT / "data" / "outputs" / f"refusal_directions_{size}.pt"
        if refusal_path.exists() and not args.force:
            skip("Refusal directions",
                 f"{refusal_path.name} exists (use --force to recompute)",
                 timings, log)
        else:
            cmd = [py, "scripts/04_compute_refusal_directions.py", "--size", size]
            if not run(cmd, plan[idx - 1][0], idx, total, plan[idx - 1][1], log, timings):
                log.close()
                final_summary(timings, time.monotonic() - t_start, log_path, ok=False)
                sys.exit(1)
        idx += 1

        # 5b. Silhouette
        sil_cmd = [py, "scripts/05_silhouette_scores.py", "--size", size]
        if size in CLOUD_SIZES:
            sil_cmd.append("--force")
        if not run(sil_cmd, plan[idx - 1][0], idx, total, plan[idx - 1][1], log, timings):
            log.close()
            final_summary(timings, time.monotonic() - t_start, log_path, ok=False)
            sys.exit(1)
        idx += 1

    # 6. Status
    if not run([py, "scripts/00_status.py"], plan[idx - 1][0], idx, total, plan[idx - 1][1],
               log, timings):
        log.close()
        final_summary(timings, time.monotonic() - t_start, log_path, ok=False)
        sys.exit(1)

    total_elapsed = time.monotonic() - t_start
    log.event("run_end", status="ok", elapsed_s=int(total_elapsed))
    log.close()
    final_summary(timings, total_elapsed, log_path, ok=True)


if __name__ == "__main__":
    main()
