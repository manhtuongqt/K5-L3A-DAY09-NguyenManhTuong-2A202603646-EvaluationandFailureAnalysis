"""Reproduce Day09 public evidence; no report is edited after generation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("core", "advanced", "final"), required=True)
    ap.add_argument("--refresh-manifest", action="store_true",
                    help="refresh artifact hashes for already recorded commands; does not change eval metrics")
    args = ap.parse_args()
    os.chdir(SRC)
    logs = ROOT / "docs/evidence/day09"
    logs.mkdir(parents=True, exist_ok=True)
    records = []

    def run(name, argv, expected=0):
        proc = subprocess.run([sys.executable, "-X", "utf8", *argv], cwd=SRC,
                              env={**os.environ, "PYTHONUTF8": "1"},
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        body = "$ python " + " ".join(argv) + "\n" + proc.stdout + proc.stderr + f"\nexit_code={proc.returncode}\n"
        (logs / (name + ".txt")).write_text(body, encoding="utf-8")
        records.append({"name": name, "argv": argv, "expected_exit": expected,
                        "exit_code": proc.returncode, "passed": proc.returncode == expected})
        print(f"{name}: exit {proc.returncode}, expected {expected}", flush=True)
        if proc.returncode != expected:
            print(proc.stdout[-6000:] + proc.stderr[-3000:], flush=True)
            write()
            raise SystemExit(1)

    def write():
        report_dir = SRC / "reports"
        report_dir.mkdir(exist_ok=True)
        def in_scope(p):
            if args.phase == "core":
                return p.stem in {"baseline_v1", "eval_fixed", "eval_seeded_regression", "eval_pr"}
            if args.phase == "advanced":
                return p.stem == "baseline_v2" or p.stem.endswith("_v2")
            return p.name.startswith(("baseline_v", "eval_fixed", "eval_seeded", "eval_slice", "eval_flaky", "eval_honest"))
        data = {"phase": args.phase, "commands": records, "passed": all(r["passed"] for r in records),
                "artifacts": {str(p.relative_to(SRC)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(report_dir.glob("*.json"))
                              if in_scope(p)}}
        (report_dir / f"day09_verification_{args.phase}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def ev(shape, spec, out):
        run("eval_" + out, ["-m", "lab9.eval", "--shape", shape, "--spec", f"config/{spec}.yaml",
                           "--out", f"reports/{out}.json"])

    def ga(name, report, version, expected=0, *extra):
        run(name, ["-m", "lab9.gate", "--pr", f"reports/{report}.json",
                   "--baseline", f"reports/baseline_{version}.json",
                   "--spec", f"config/metric_spec{'_v2' if version == 'v2' else ''}.yaml", *extra], expected)

    if args.refresh_manifest:
        records.extend(json.loads((SRC / f"reports/day09_verification_{args.phase}.json").read_text(encoding="utf-8"))["commands"])
        write()
        print("refreshed artifact manifest for", args.phase)
        return 0
    if args.phase == "core":
        run("m0_smoke", ["-m", "lab9.smoke"])
        run("m1_evalset_v1", ["-m", "lab9.evalset", "--build", "--check"])
        run("core_tests", ["-m", "pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "lab9 and not advanced"])
        run("evalset_cli_tests", ["-m", "pytest", "-q", "-o", "addopts=", "tests/test_lab9_evalset.py"])
        run("m2_tone", ["-m", "lab9.judge", "--csv", "data/eval/judge_tone_public.csv", "--audit", "10"])
        run("m2_helpful", ["-m", "lab9.judge", "--csv", "data/eval/judge_helpful_public.csv", "--audit", "5"], 1)
        for shape in ("seeded_regression", "fixed"):
            run("trace_C002_" + shape, ["-m", "lab9.trace_case", "--shape", shape, "--claim", "C-002", "--seed", "11"])
        run("m3_detection", ["-m", "lab9.mutation", "--detect"])
        ev("swarm", "metric_spec", "baseline_v1")
        for shape in ("fixed", "seeded_regression"):
            ev(shape, "metric_spec", "eval_" + shape)
        ev("swarm", "metric_spec", "eval_pr")
        for shape in ("fixed", "seeded_regression", "pr"):
            ga("m4_gate_" + shape, "eval_" + shape, "v1", 1 if shape == "seeded_regression" else 0)
        ga("m4_baseline_self", "baseline_v1", "v1")
        run("m4_ci_check", ["-m", "lab9.ci_check", "--pr", "reports/eval_pr.json",
                           "--baseline", "reports/baseline_v1.json", "--spec", "config/metric_spec.yaml"])
    elif args.phase == "advanced":
        run("m5_evalset_v2", ["-m", "lab9.evalset", "--v2", "--build"])
        run("advanced_tests", ["-m", "pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "advanced"])
        run("m6_aa", ["-m", "lab9.mutation", "--spec", "config/metric_spec_v2.yaml", "--aa", "66,77,88,99,110"])
        ev("swarm", "metric_spec_v2", "baseline_v2")
        for shape in ("fixed", "honest_refactor", "seeded_regression", "slice_regression", "flaky_regression"):
            ev(shape, "metric_spec_v2", "eval_" + shape + "_v2")
            ga("v2_gate_" + shape, "eval_" + shape + "_v2", "v2", 0 if shape in ("fixed", "honest_refactor") else 1)
        ga("v2_baseline_self", "baseline_v2", "v2")
        run("m7_mutation", ["-m", "lab9.mutation", "--spec", "config/metric_spec_v2.yaml",
                            "--baseline", "reports/baseline_v2.json"])
        run("m7_traps", ["-m", "lab9.traps", "--pr", "reports/eval_slice_regression_v2.json",
                        "--baseline", "reports/baseline_v2.json", "--spec", "config/metric_spec_v2.yaml"])
        for trap in ("evaluator_errors_as_nan", "dropped_failing_rows", "cherry_picked_seeds", "loosened_spec"):
            extra = ["--spec", "reports/traps/loosened_spec.spec.yaml", "--base-spec", "config/metric_spec_v2.yaml"] if trap == "loosened_spec" else []
            ga("m7_trap_" + trap, "traps/" + trap, "v2", 1, *extra)
    else:
        run("host_tests", ["-m", "pytest", "-q"])
        run("day09_tests", ["-m", "pytest", "-q", "-m", "student", "-o", "addopts=", "-k", "lab9"])
        run("final_v1", ["-m", "lab9.evalset", "--check"])
        run("final_v2", ["-m", "lab9.evalset", "--v2", "--check"])
        run("final_smoke", ["-m", "lab9.smoke"])
    write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
