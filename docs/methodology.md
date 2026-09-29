# Methodology

## Module A — player similarity

**Unit.** One player, at one club, in one competition, in one season.

**Representation.** 32 per-90 behavioural features grouped into ten families: passing, progression,
creation, shooting, dribbling, defending, recoveries, receiving, aerial duels and discipline.
Goalkeepers use a separate space of nine features in three families: shot stopping, area control and
distribution. The representation is non-spatial — it contains no event coordinates, movement traces
or tactical geometry.

**Eligibility.** At least 900 minutes played, a known coarse position, at least 70% overall feature
coverage and at least 50% coverage within every family. Unknown-position observations are excluded
rather than imputed.

**Scaling.** Features are log-transformed, then centred and scaled by the median and inter-quartile
range of the same feature within the same competition, estimated on reference seasons only.

**Distance.** Equal-feature Manhattan distance: the mean absolute difference across all registered
features. Equal-feature weighting is not equal-family weighting — a family with more registered
variables contributes more total distance.

**Comparison rule.** Candidates must share the target's coarse position group. Goalkeepers are
compared only with goalkeepers.

**Evaluation.** Candidates are drawn from the earlier season and queries from the next, so retrieval
is always forward in time. The metric is Recall@10: whether a player's next-season profile places
his own previous-season profile inside the top ten. Secondary metrics are mean reciprocal rank,
median rank, coverage and subgroup breakdowns.

**Interpretation boundary.** This is a temporal self-consistency proxy. A high score means a
behavioural profile is stable enough to be recovered a season later. It is not expert-labelled
equivalence, not evidence that two different players are interchangeable, not tactical fit, and not
causal.

## Module B — post-transfer playing-time retention

**Unit.** One dated transfer from an origin club to a destination club.

**Windows.** 365 days before and 365 days after the transfer date, with at least 450 minutes in
each. Pre-window minutes count origin-club appearances only; post-window minutes count
destination-club appearances only. Events whose follow-up window extends beyond data coverage are
excluded, so the outcome is never truncated by the end of the data.

**Target.** The natural logarithm of post-transfer minutes divided by pre-transfer minutes. Positive
values mean more observed playing time after the move. Because pre-transfer minutes sit in the
denominator and also appear among the predictors, part of any apparent skill is mechanical
regression to the mean; `results/transfer_retention_metrics.csv` quantifies this through the
exposure-only reference.

**Predictors.** Pre-transfer information only: age, playing-time history, limited performance rates,
dated market value at the move, reported or estimated fee information, calendar terms, source
provenance and missingness indicators. Injury, tactical role, manager, contract, schedule and
availability context are not observed.

**Partitions.** Chronological, with earliest-partition-wins player isolation so that no player
appears in more than one partition. Imputation and scaling are fitted on the training partition only,
inside the model pipeline.

**Model.** Ordinary least squares, fitted on the training partition and not refitted before the
held-out evaluation.

**Baselines.** Four transparent rules, all fixed before the evaluation and parameterized on training
data only: predict no change; the training median; the median within pre-transfer minute bands; and
the median within age-by-minute bands. Definitions are in `src/retention_baselines.py`.

**Post-hoc reference.** A one-variable ordinary least-squares model using prior playing time alone
was added *after* the evaluation, to bound the interpretation of the baseline comparison. It is
labelled post-hoc everywhere it appears and is not a baseline.

**Interpretation boundary.** The target is playing-time retention, an opportunity measure. It is not
player quality, tactical fit, transfer success, market value, transfer fee, or a causal destination
effect.

## Uncertainty

Intervals are 95% bootstrap intervals resampled by player, so repeated observations of the same
player stay grouped. They are descriptive intervals, not formal hypothesis tests.

## Evidence layers

Results are labelled by how they were produced.

| Layer | Meaning |
| --- | --- |
| Held-out | Produced by the single evaluation opened once, on data untouched during development |
| Post-hoc | Computed after that evaluation was opened; diagnostic, never independent validation |
| Derived | Arithmetic on published values, such as the chance retrieval rate |

Every row in `results/` carries its evidence layer.
