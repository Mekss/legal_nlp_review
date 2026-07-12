# Corpus audit report (semi-automatic curation)

- documents scored (unfiltered corpus): **3697**; known noise from the manual round: 55 docs.
- **blind recovery**: median outlier percentile of known noise **3** (0 = most anomalous); **100%** of known noise sits in the bottom 10% of the ranking (random baseline: 10%).
- workflow for a NEW topic: run this notebook -> verify the 40-row shortlist (YES/NO) -> add confirmed exclusions to the corpus-build filters. Flagging is automated; only verification is human.
- channels are topic-agnostic: metadata structure scan + embedding outlier geometry; no lexicons, no rules.
