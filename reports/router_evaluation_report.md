# Router evaluation report (RQ1 — capability boundary)

- gold set: **60** questions (frozen: `router_gold_questions.csv`), 20 per bucket, 30 German / 30 English
- router: the deployed Layer-1 detector exec'd from `rag_echr_ris.ipynb` (36 patterns, binary retrieval-vs-aggregate)

## Headline numbers
- routing accuracy: **0.950**
- fabrication risk (Bucket-3 sent to retrieval): **0.100** (2/20)
- over-abstention (Bucket-1 refused): **0.000** (0/20)

## Accuracy per bucket x language

| bucket | de | en |
|---|---|---|
| 1 | 1.0 | 1.0 |
| 2 | 1.0 | 0.9 |
| 3 | 0.9 | 0.9 |

## Failures (verbatim)

- **FABRICATION RISK** (bucket 3, en): “Do married parents win contact disputes more often than unmarried ones?”
- **FABRICATION RISK** (bucket 3, de): “Welcher Elternteil wird in den meisten Fällen für die Entfremdung verantwortlich gemacht?”
- **missed aggregate** (bucket 2, en): “Which importance level is most common among the judgments?”

## Why n=60 (design + statistics)
- 60 = 3 buckets × 2 languages × 10 hand-authored questions: equal-weight cells; 10 non-redundant *hard* items per cell is the practical authoring bound.
- What n=60 buys (95% Wilson): accuracy 0.95 → CI [0.86, 0.98]; fabrication risk 0.10 at per-bucket n=20 → CI [0.03, 0.30] — stated, not hidden: the headline is tight, per-bucket rates are indicative. The gold set is a frozen CSV; it can be grown without invalidating prior runs.

## Reading
- The router is binary by design; Bucket 2 vs 3 is separated downstream by the query layer (which knows the validated columns). This report measures the boundary that matters for faithfulness: **no aggregate question may reach generation**.
- Failures where aggregate intent carries no lexical trigger (e.g. “most common”, “more often than”) are the known limit of a pattern router — candidates for a semantic-routing extension, or reported as a stated limitation.
