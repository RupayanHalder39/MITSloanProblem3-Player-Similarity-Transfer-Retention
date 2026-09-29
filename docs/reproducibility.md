# Reproducibility

**Status: PARTIAL.**

Three different things are sometimes called "reproduction". This repository supports the first two
and not the third, and the distinction matters.

| Level | Supported here | What it means |
| --- | --- | --- |
| Figure reproduction | **Yes, fully portable** | Both paper figures regenerate exactly from the published aggregate tables |
| Metric verification | **Yes, fully portable** | Published numbers can be checked against the paper and against each other |
| Full model reproduction | **No** | Re-estimating the models requires the restricted source data |

Regenerating two figures is not the same as reproducing the study, and this repository does not
present it as such.

## Environment

Python 3.11 or later. Dependencies are listed in `requirements.txt` and are deliberately minimal:
pandas, numpy and matplotlib.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Figure reproduction

```bash
python src/build_figures.py
```

Reads `results/context_sensitivity.csv` and `results/transfer_retention_metrics.csv` and writes both
figures as PNG and SVG into `figures/`. No restricted data is touched, and no network access is
needed. The output should be byte-comparable in content to the figures already committed and
identical to the figures printed in the paper.

To write elsewhere without overwriting the committed files:

```bash
python src/build_figures.py --output-dir /tmp/figures
```

## Metric verification

```bash
python scripts/verify_release.py
```

This checks that the published aggregate tables carry the values stated in the paper, that the
repository contains no restricted data or secrets, that README links resolve, that `CITATION.cff`
parses, and that every Python file compiles. It depends only on this repository — it does not read
the private research project.

## Full model reproduction

Not possible from the published material. It requires:

- a licensed copy of the SoccerSolver match and player-season export;
- the `dcaribou/transfermarkt-datasets` snapshot for the same period, under a rights position that
  permits the intended use;
- the canonical build, evaluation and robustness code held in the private research project.

The scientific definitions needed to rebuild the analysis are public here: `src/core_definitions.py`,
`src/similarity_distance.py` and `src/retention_baselines.py` contain the per-90 rates, robust
scaling, distance, retention target, eligibility predicates, feature families and the four pre-set
baselines. See `docs/data_provenance.md`.

## Determinism in the original study

The original pipeline was deterministic: fixed random seeds, exact-match identity rules with no fuzzy
matching, hash-verified frozen inputs, and a held-out evaluation gated on those hashes and opened
once. Bootstrap intervals were computed with a fixed seed and resampled by player.
