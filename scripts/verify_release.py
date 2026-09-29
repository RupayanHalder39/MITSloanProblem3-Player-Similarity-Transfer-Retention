#!/usr/bin/env python3
"""Release checks for the public repository.

Verifies that the repository is complete, portable, free of restricted material, and that the
published aggregate numbers match the values stated in the paper. Depends only on this repository.

Usage:
    python scripts/verify_release.py
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md", "LICENSE", "CITATION.cff", "requirements.txt", ".gitignore",
    "PUBLIC_RELEASE_AUDIT.md",
    "assets/RupayanHalder.jpeg", "assets/SoccerSolverLogo.png",
    "docs/data_provenance.md", "docs/limitations.md", "docs/methodology.md",
    "docs/reproducibility.md",
    "figures/figure_1_similarity_exposure_tradeoff.png",
    "figures/figure_1_similarity_exposure_tradeoff.svg",
    "figures/figure_2_transfer_retention_model_comparison.png",
    "figures/figure_2_transfer_retention_model_comparison.svg",
    "paper/Problem3_Beyond_Like_for_Like.pdf",
    "results/similarity_metrics.csv", "results/context_sensitivity.csv",
    "results/transfer_retention_metrics.csv",
    "src/build_figures.py", "src/core_definitions.py",
    "src/retention_baselines.py", "src/similarity_distance.py",
]

# Values as printed in the paper. Each is checked against results/ to 3 decimal places.
PAPER_VALUES = {
    "similarity_metrics.csv": {
        "queries_held_out": 6524, "recall_at_10": 0.219,
        "recall_at_10_goalkeeper": 0.099, "recall_at_10_outfield": 0.237,
        "candidate_pool_median": 5884, "chance_recall_at_10": 0.002,
    },
    "transfer_retention_metrics.csv": {
        "transfers_held_out": 1724, "mae_full_model": 0.433,
        "spearman_full_model": 0.638, "mae_baseline_minute_band_median": 0.479,
        "improvement_pct_vs_strongest_baseline": 9.66,
        "mae_exposure_only_reference": 0.452,
        "improvement_pct_vs_exposure_only": 4.3,
        "mae_increase_pct_validation_to_test": 6.9,
        "mean_bias_full_model": 0.141,
        "largest_errors_sharp_decline_overpredictions": 19,
    },
}
PAPER_CONTEXT = {
    "same club, same competition": 0.305,
    "different club, same competition": 0.139,
    "different club, different competition": 0.066,
    "450 minutes": 0.156, "900 minutes": 0.219, "1350 minutes": 0.286,
}
PAPER_CONTEXT_N = {"450 minutes": 11078, "900 minutes": 6524, "1350 minutes": 3718}

FORBIDDEN_SUFFIXES = {".parquet", ".db", ".sqlite", ".duckdb", ".joblib", ".pkl", ".pickle",
                      ".csv.gz", ".sql", ".env"}
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|private[_-]?key)\b\s*[:=]"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
TEXT_SUFFIXES = {".md", ".py", ".csv", ".cff", ".txt", ".yml", ".yaml", ".toml", ".gitignore"}
# Assembled at runtime so this probe never matches its own source.
HOME_PREFIX = "/" + "Users" + "/"

results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append(("PASS" if ok else "FAIL", name, detail))


def repo_files() -> list[Path]:
    return [p for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts and ".venv" not in p.parts]


def load_csv(name: str) -> dict:
    import csv
    with (ROOT / "results" / name).open(newline="", encoding="utf-8") as handle:
        return {row["metric"]: row for row in csv.DictReader(handle)}


def main() -> None:
    files = repo_files()

    missing = [name for name in REQUIRED if not (ROOT / name).exists()]
    check("required files present", not missing, f"missing: {missing or 'none'}")

    symlinks = [str(p.relative_to(ROOT)) for p in files if p.is_symlink()]
    symlinks += [str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
                 if p.is_symlink() and ".git" not in p.parts]
    check("no symlinks", not symlinks, f"found: {sorted(set(symlinks)) or 'none'}")

    restricted = [str(p.relative_to(ROOT)) for p in files
                  if p.suffix.lower() in FORBIDDEN_SUFFIXES
                  or "".join(p.suffixes[-2:]).lower() == ".csv.gz"]
    check("no restricted data formats", not restricted, f"found: {restricted or 'none'}")

    text_files = [p for p in files if p.suffix.lower() in TEXT_SUFFIXES or p.name == ".gitignore"]
    secrets = []
    absolute = []
    for path in text_files:
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            secrets.append(str(path.relative_to(ROOT)))
        if HOME_PREFIX in content:
            absolute.append(str(path.relative_to(ROOT)))
    check("no obvious secrets", not secrets, f"found: {secrets or 'none'}")
    check("no absolute local paths", not absolute, f"found: {absolute or 'none'}")

    oversized = [f"{p.relative_to(ROOT)} ({p.stat().st_size / 1e6:.1f} MB)"
                 for p in files if p.stat().st_size > 5_000_000]
    check("no unexpectedly large files", not oversized, f"over 5 MB: {oversized or 'none'}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"]\((?!https?://|mailto:)([^)#]+)\)", readme)
    links += re.findall(r'src="([^"]+)"', readme)
    broken = sorted({link for link in links if not (ROOT / link).exists()})
    check("README local links resolve", not broken, f"broken: {broken or 'none'}")

    compiled, failed = 0, []
    for path in files:
        if path.suffix == ".py":
            try:
                ast.parse(path.read_text(encoding="utf-8"))
                compiled += 1
            except SyntaxError as error:
                failed.append(f"{path.relative_to(ROOT)}: {error}")
    check("Python files compile", not failed, f"{compiled} compiled; failures: {failed or 'none'}")

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    has_keys = all(key in citation for key in ("cff-version:", "title:", "authors:", "license:"))
    check("CITATION.cff parses", has_keys and "Beyond Like-for-Like" in citation,
          "required keys and the paper title present")

    paper = ROOT / "paper/Problem3_Beyond_Like_for_Like.pdf"
    check("paper is a readable PDF",
          paper.exists() and paper.read_bytes()[:5] == b"%PDF-",
          f"{paper.stat().st_size / 1e6:.2f} MB" if paper.exists() else "missing")

    mismatches = []
    for filename, expected in PAPER_VALUES.items():
        table = load_csv(filename)
        for metric, want in expected.items():
            if metric not in table:
                mismatches.append(f"{filename}:{metric} absent")
                continue
            got = float(table[metric]["value"])
            decimals = len(str(want).split(".")[1]) if "." in str(want) else 0
            if round(got, decimals) != round(float(want), decimals):
                mismatches.append(f"{filename}:{metric} published {got:.4f}, paper {want}")
    check("aggregate metrics match the paper", not mismatches,
          f"{sum(len(v) for v in PAPER_VALUES.values())} values checked; "
          f"mismatches: {mismatches or 'none'}")

    import csv as csv_module
    with (ROOT / "results/context_sensitivity.csv").open(newline="", encoding="utf-8") as handle:
        context = {row["stratum"]: row for row in csv_module.DictReader(handle)}
    context_bad = []
    for stratum, want in PAPER_CONTEXT.items():
        if stratum not in context:
            context_bad.append(f"{stratum} absent")
            continue
        got = round(float(context[stratum]["recall_at_10"]), 3)
        if abs(got - want) > 0.0006:
            context_bad.append(f"{stratum} published {got}, paper {want}")
    for stratum, want in PAPER_CONTEXT_N.items():
        if stratum in context and int(context[stratum]["n"]) != want:
            context_bad.append(f"{stratum} n published {context[stratum]['n']}, paper {want}")
    check("context and exposure values match the paper", not context_bad,
          f"{len(PAPER_CONTEXT) + len(PAPER_CONTEXT_N)} values checked; "
          f"mismatches: {context_bad or 'none'}")

    # Overstatement screen. The public documents deliberately *deny* several of these claims, so a
    # bare substring search would flag its own disclaimers. Each hit is therefore checked for a
    # negation in the preceding clause and only counted when the phrase is used assertively.
    claim_phrases = [
        "we recommend signing", "should sign", "should not sign",
        "proves that", "guarantees that", "demonstrates causation",
        "players are interchangeable", "are equivalent replacements",
        "combined recruitment score", "overall recruitment rating",
        "predicts transfer success", "causal effect of the destination",
    ]
    negations = ("not", "never", "no ", "nor ", "neither", "without", "rather than",
                 "cannot", "does not", "do not", "is not", "are not")
    asserted = []
    for path in text_files:
        if path.suffix not in {".md", ".cff"}:
            continue
        content = path.read_text(encoding="utf-8").lower().replace("\n", " ")
        for phrase in claim_phrases:
            start = 0
            while (index := content.find(phrase, start)) != -1:
                window = content[max(0, index - 90):index]
                if not any(token in window for token in negations):
                    asserted.append(f"{path.relative_to(ROOT)}: '{phrase}'")
                start = index + len(phrase)
    check("no overstated or causal claims", not asserted,
          f"{len(claim_phrases)} phrases screened with negation context; "
          f"asserted uses: {asserted or 'none'}")

    public_text = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in text_files if path.suffix in {".md", ".cff"})
    for phrase in ["temporal self-consistency", "not redistribut", "partial"]:
        check(f"claim boundary stated: '{phrase}'", phrase in public_text, "present in public docs")

    width = max(len(name) for _, name, _ in results)
    print("Release verification\n" + "=" * (width + 40))
    for status, name, detail in results:
        print(f"[{status}] {name.ljust(width)}  {detail}")
    failures = [r for r in results if r[0] == "FAIL"]
    print("=" * (width + 40))
    print(f"{len(results) - len(failures)} passed, {len(failures)} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
