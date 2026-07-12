# Citation structure report (topic-agnostic Bucket-2 family)

## ECHR precedent network
- coverage: 414/1116 cases carry `scl` citations (37%); 7293 citation edges, 3346 distinct precedents.
- top precedents: **Hokkanen v. Finland** (75); **Kutzner v. Germany** (56); **Elsholz v. Germany [GC]** (55); **Ignaccolo-Zenide v. Romania** (54); **Keegan v. Ireland** (52)
- precedent age at citation: median **8 years** (p90 21) -- the Court builds on settled law.
- figure: `figures/echr_precedent_network.png`

## Austrian principle lifecycles
- 38 Rechtssaetze with dated applications; median active span **30 years** (max 70).
- living law: **27/38** principles applied since 2021.
- figure: `figures/ris_principle_lifecycles.png`

## Reusability note
Both analyses consume only structured citation metadata captured by the generic importer -- they run **unchanged** on any topic corpus from these sources. Caveats: `scl` coverage is partial and biased toward judgments; RIS application lists come from RIS's own linkage; counts describe the keyword-matched corpus.
