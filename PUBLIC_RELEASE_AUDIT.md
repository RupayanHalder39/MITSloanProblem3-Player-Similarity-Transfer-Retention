# Public release audit

Record of the checks run before this repository was published. Re-runnable at any time with
`python scripts/verify_release.py`.

**Release date:** 2026-09-29
**Verdict:** approved for public release, with data redistribution deliberately excluded.

## Scope

The repository is a curated public release, not a copy of the private research project. The private
project contains restricted source data, canonical row-level datasets, fitted model artifacts, and
internal audit material. None of that is published here.

## Data and licensing

| Item | Decision | Reason |
| --- | --- | --- |
| Transfermarkt-derived tables | **Excluded** | Upstream rights unresolved; the CC0 declaration covers the packaging project, not the underlying records |
| SoccerSolver match and player-season export | **Excluded** | No documented redistribution licence |
| Canonical player-season and transfer records | **Excluded** | Row-level data on identifiable players and clubs, derived from both restricted sources |
| Identity bridge tables | **Excluded** | Row-level player and club linkage |
| Held-out predictions | **Excluded** | One row per identifiable transfer |
| Fitted model artifacts | **Excluded** | Serialized estimators fitted on restricted data |
| Aggregate result tables | **Included** | Small summary statistics only; no row-level information |
| Both paper figures | **Included** | Aggregate visualisations, regenerable from the included tables |
| Definition modules | **Included** | Pure functions and constants; no data |

Consequence: **Reproducibility status is PARTIAL.** Figure reproduction and metric verification are
portable; end-to-end model re-estimation is not. This is stated in the README, in
`docs/reproducibility.md` and in `docs/data_provenance.md`, and is not overstated anywhere.

## Safety checks

| Check | Result |
| --- | --- |
| Secrets, credentials, tokens, private keys | None found |
| Absolute local filesystem paths in published files | None |
| Symbolic links | None; the paper, images and code are physical copies |
| Restricted data formats (`.parquet`, `.sql`, `.csv.gz`, `.db`, `.sqlite`, `.duckdb`, `.joblib`, `.pkl`) | None present, and all are excluded by `.gitignore` |
| Unexpectedly large files | None above 5 MB; the largest file is the paper at 1.14 MB |
| Caches, temporary files, `__pycache__`, `.DS_Store` | None committed; excluded by `.gitignore` |
| Reviewer comments, internal correspondence, private discussions | None present |
| Previous manuscript versions, superseded abstracts, rejected figures | None present; only the final submitted paper |
| Internal audit and stage logs | Not published |
| Copyrighted broadcast or third-party imagery | None. The only images are the researcher photograph and the SoccerSolver logo, both included deliberately for attribution |
| Machine-specific assumptions | None; the figure builder and validator use paths relative to the repository root |

## Content checks

| Check | Result |
| --- | --- |
| Required files present | All 23 present |
| README internal links resolve | All resolve |
| Python files compile | 5 of 5 |
| `CITATION.cff` parses and carries the final paper title | Yes |
| Paper opens as a valid 2-page PDF | Yes |
| Both figures present as PNG and SVG | Yes, regenerated from `results/` rather than extracted from the PDF |
| Figures reproducible from published data alone | Yes, via `python src/build_figures.py` |
| `requirements.txt` minimal | Three packages |

## Scientific consistency

Every published aggregate value was checked against the final paper. **25 values verified, zero
mismatches.**

Module A: 6,524 held-out queries · Recall@10 0.219 (95% CI 0.209–0.229) · median candidate pool
5,884 · chance retrieval ≈0.002 · context strata 0.305 / 0.165 / 0.139 / 0.066 · goalkeepers 0.099
against outfield 0.237 · exposure sensitivity 0.156 / 0.219 / 0.286 at 11,078 / 6,524 / 3,718
eligible profiles.

Module B: 1,724 held-out transfers · MAE 0.433 (95% CI 0.417–0.448) · Spearman 0.638 · strongest
pre-set baseline 0.479 · improvement 9.66% (95% CI 7.8–11.6%) · post-hoc exposure-only reference
0.452 · additional gain 4.31% · validation-to-held-out error increase 6.86% · mean bias +0.141 · 19
of the 20 largest errors were over-predicted sharp declines.

Two values are printed to more precision in `results/` than in the paper, which rounds them:
`improvement_pct_vs_exposure_only` is 4.308% (paper: 4.3%) and
`mae_increase_pct_validation_to_test` is 6.857% (paper: 6.9%). The published tables carry the exact
computed values; no discrepancy exists.

## Claim boundaries

| Boundary | Status |
| --- | --- |
| No combined recruitment score | Enforced; the separation is argued explicitly in the README |
| No player-equivalence claim | Enforced; retrieval is described as a temporal self-consistency proxy throughout |
| No transfer-success claim | Enforced; the target is described as playing-time retention, an opportunity measure |
| No causal claim | Enforced; all associations are labelled predictive and descriptive |
| No automatic signing recommendation | Enforced; human judgement is stated as retained at every point |
| Post-hoc evidence labelled | Enforced; every row in `results/` carries its evidence layer |
| Limitations disclosed | 22 registered limitations in `docs/limitations.md`, summarised in the README |

An automated screen for assertive overstatement found none.

## Outstanding

- The complete author list is not finalized. `CITATION.cff` carries an explicit placeholder and no
  claim of sole authorship is made.
- No DOI, paper identifier or acceptance status is asserted anywhere.
- Data redistribution remains unavailable pending separate authorization.
