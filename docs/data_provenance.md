# Data provenance

## Summary

**No raw or derived row-level data is published in this repository.** Only small aggregate result
tables appear, under `results/`. This document records where the data came from, why it is not
redistributed, and what an authorized researcher would need in order to reconstruct the analysis.

## Sources used

### 1. Transfermarkt-derived transfer, appearance and match data

Obtained through the open `dcaribou/transfermarkt-datasets` project as a dated, hash-frozen
snapshot. Four tables supplied transfer events, player identities, club identities and competition
metadata; two further tables supplied historical appearances and games for the playing-time windows.

The repository declares **CC0-1.0** for its own packaging. The underlying records are
Transfermarkt-derived, and that upstream rights position is **not resolved**. The project retained
this uncertainty explicitly rather than treating the CC0 declaration as sufficient to redistribute.

### 2. SoccerSolver match and player-season export

An internal export providing player-season behavioural statistics and player-match records. It
carries **no documented redistribution licence**. It is the source of the per-90 behavioural
features used by the similarity module.

## How the data was processed, conceptually

1. **Identity resolution.** Players, clubs and competitions were linked between the two sources
   using deterministic exact rules only. Shared numeric identifiers were tested semantically and
   rejected where concordance fell below 95%. No fuzzy matching was used, and unresolved entities
   were dropped rather than guessed.
2. **Similarity records.** Each player-club-competition-season row carries raw action counts and
   per-90 rates, exposure, position, goalkeeper status and missingness flags.
3. **Transfer records.** Each dated transfer event was given a 365-day window on either side.
   Pre-window minutes count origin-club appearances only; post-window minutes count destination-club
   appearances only. Events whose 365-day follow-up extended beyond data coverage were excluded.
4. **Partitions.** Both modules use chronological splits. The transfer partitions additionally apply
   earliest-partition-wins player isolation, so no player appears in more than one partition.
5. **Aggregation.** Only the resulting aggregate metrics — counts, means, correlations and bootstrap
   intervals — are published here.

## What is omitted, and why

| Omitted | Reason |
| --- | --- |
| Raw Transfermarkt-derived tables | Upstream rights unresolved |
| SoccerSolver export | No redistribution licence |
| Canonical player-season records | Derived from both restricted sources; row-level player data |
| Canonical transfer records | Row-level transfer data covering identifiable players and clubs |
| Identity bridge tables | Row-level player and club linkage |
| Held-out predictions | Row-level, one row per identifiable transfer |
| Fitted model artifacts | Serialized estimators fitted on restricted data |

## What an authorized researcher would need

Reconstructing the full pipeline requires:

1. A licensed copy of the SoccerSolver match and player-season export.
2. The `dcaribou/transfermarkt-datasets` snapshot for the same period, with a rights position that
   permits the intended use.
3. The canonical build, evaluation and robustness code, which is held in the private research
   project and can be shared on request subject to the same data conditions.

Given those inputs, the definitions needed to rebuild the analysis are public in this repository:
`src/core_definitions.py` (per-90 rates, robust scaling, distance, retention target, eligibility),
`src/similarity_distance.py` (feature families, coverage rules, normalizer) and
`src/retention_baselines.py` (the four pre-set baselines).

## Honest statement of reproducibility

**Reproducibility status: PARTIAL.** Figure reproduction and metric verification are fully portable
from this repository. End-to-end model re-estimation is not possible from the published material
alone. This repository does not claim otherwise.
