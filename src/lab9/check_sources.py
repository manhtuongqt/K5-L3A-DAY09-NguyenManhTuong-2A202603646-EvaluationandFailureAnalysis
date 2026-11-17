"""Check immutable source boundaries, submission artifacts and common secret patterns."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import yaml

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
BASE = "d1b9471540727d693c9eb392667b9f0d8a998bf5"


def digest(data):
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def main():
    lock = json.loads((SRC / "config/day09_source_lock.json").read_text(encoding="utf-8"))
    errors = []
    protected_sources = {**lock["protected_starter_files"], **lock["protected_day08_files"]}
    for relative, expected in protected_sources.items():
        p = ROOT / relative
        if not p.is_file() or digest(p.read_bytes()) != expected:
            errors.append("changed starter source: " + relative)
    expected_lab8 = {p for p in lock["protected_day08_files"] if p.startswith("src/lab8/")}
    actual_lab8 = {str(p.relative_to(ROOT)).replace("\\", "/") for p in (SRC / "lab8").rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if actual_lab8 != expected_lab8:
        errors.append("Day08 lab8 file set changed: " + repr(sorted(actual_lab8 ^ expected_lab8)))
    harness = yaml.safe_load((SRC / "harness_map.yaml").read_text(encoding="utf-8"))
    section = harness.get("sections", {}).get("orchestration")
    section_sha = hashlib.sha256(json.dumps(section, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if section_sha != lock["day08_orchestration_sha256"]:
        errors.append("original orchestration section changed in harness_map")
    names = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    forbidden = [x for x in names if any(s in x.split("/") for s in (".venv", ".env", "traces", "student_drop"))
                 or x.endswith((".sqlite", ".key", ".pem")) or x.startswith("src/eval/instructor/")]
    if forbidden:
        errors.append("tracked private/runtime paths: " + repr(forbidden))
    patterns = [rb"sk-(?:proj-)?[A-Za-z0-9_-]{24,}", rb"gh[pousr]_[A-Za-z0-9]{20,}",
                rb"AIza[0-9A-Za-z_-]{30,}", rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]
    introduced = subprocess.run(["git", "diff", "--name-only", BASE], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.splitlines()
    for name in introduced:
        p = ROOT / name
        if p.is_file() and any(re.search(pattern, p.read_bytes()) for pattern in patterns):
            errors.append("possible credential: " + name)
    for version in ("v1", "v2"):
        path = SRC / f"data/eval/eval_set_{version}.jsonl"
        report = SRC / f"reports/baseline_{version}.json"
        if path.is_file() and report.is_file():
            expected = json.loads(report.read_text(encoding="utf-8"))["manifest"]["eval_set_sha"]
            if hashlib.sha256(path.read_bytes()).hexdigest()[:12] != expected:
                errors.append("baseline eval-set SHA mismatch: " + version)
    summary = {"protected_starter_files": len(lock["protected_starter_files"]),
               "protected_day08_files": len(lock["protected_day08_files"]),
               "day08_repository": lock["day08_repository"], "day08_commit": lock["day08_commit"],
               "day09_starter_commit": BASE, "changed_paths_scanned": len(introduced),
               "tracked_paths_scanned": len(names), "errors": errors,
               "scope": "source boundary and common credential patterns; not a proof of no vulnerabilities"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
