# Limitations

Stated plainly. Several of these are the most informative part of the study.

## Module A — player similarity

1. **The target is a proxy.** Same-player next-season retrieval measures whether a behavioural
   fingerprint is stable, not whether two different players are equivalent. There is no
   expert-labelled equivalence set to validate against, and this cannot be fixed by analysis.
2. **Retrieval is weakest where recruitment operates.** Recall@10 falls from 0.305 when club and
   competition are unchanged to 0.066 when both change — a median rank of 496 in a pool whose median
   size is 5,884. The recruitment case is the weakest case measured.
3. **Goalkeeper representation is thin.** Nine features in three families, most with little usable
   spread across the pool. Goalkeeper retrieval of 0.099 is a statement about the available
   goalkeeping data, not about goalkeepers.
4. **The headline depends on the eligibility rule.** Recall@10 moves from 0.156 to 0.286 across the
   450, 900 and 1,350-minute thresholds while eligible profiles fall from 11,078 to 3,718. Any club
   adopting a different threshold should expect a different number.
5. **The representation is non-spatial.** No event coordinates, movement or tactical geometry.
6. **Equal-feature weighting is not equal-family weighting.** Families with more registered
   variables contribute more total distance.
7. **Unknown-position observations are excluded**, so the evaluated population is not the full
   player population.

## Module B — playing-time retention

8. **The outcome is opportunity, not quality.** Playing time reflects role, fitness, squad
   competition and manager preference as well as ability. It is not transfer success or tactical fit.
9. **Part of the skill is mechanical.** Pre-transfer minutes sit in the denominator of the target
   and also appear among the predictors. A post-hoc reference using prior playing time alone reaches
   MAE 0.452 against the full model's 0.433, so the richer feature set adds about 4.3% beyond
   exposure regression to the mean, against 9.66% versus the strongest pre-set baseline.
10. **Performance degrades over time.** Error rises 6.9% from validation to the held-out set and
    mean bias more than doubles, to +0.141. The model would need periodic refitting.
11. **Sharp declines are systematically over-predicted.** 19 of the 20 largest errors are sharp
    playing-time declines the model missed — the case most worth flagging is the one it most
    reliably misses.
12. **Critical context is unobserved.** Injury, tactical role, manager, contract, schedule and
    availability are not in the data at all.
13. **Transfer type is not reliably observed.** Loans and permanent moves are not distinguished, and
    no inference from fee was permitted.
14. **Fee figures are reported or estimated**, never audited transaction consideration.
15. **Player isolation narrows the evaluation.** Earliest-partition-wins isolation removes later
    events for players already seen, so the evaluated cohort is not a random sample of transfers.

## Joint

16. **No combined score.** The two modules answer different questions on different units with
    incommensurable scales. A distance in standardized behaviour units cannot be added to a log
    minutes ratio.
17. **No causal claim.** No destination, club, league, age, fee or transfer-type effect is
    identified. Every reported association is predictive and descriptive.
18. **No signing recommendation.** Nothing here supports an automatic buy or do-not-buy decision.
19. **Coverage is not a defined sampling frame.** The competition universe is broad but
    opportunistic, so generalization beyond the observed competitions is not supported.
20. **Post-hoc analyses are not validation.** Diagnostics computed after the held-out evaluation was
    opened are labelled as such throughout and never presented as independent confirmation.
21. **Intervals are descriptive.** Player-clustered bootstrap intervals, not formal hypothesis tests.
22. **Data is not redistributable**, so independent end-to-end reproduction is blocked. See
    `docs/data_provenance.md`.
