# Retrieval evaluation report (RQ1 ranking quality / RQ4 cross-lingual)

- index: **42055** chunks (ECHR EN + RIS AT + Swiss CH), top-6, genre-filtered + MMR (deployed settings)
- query set: **24** frozen Bucket-1 queries (16 DE / 8 EN)

## Jurisdiction mix of retrieved hits by query language

```
jurisdiction  AT (OGH)  CH  ECHR
query_lang                      
de                  33  63     0
en                   0   0    48
```

## ECHR section composition
- LAW share of ECHR hits: **0.23** (LAW = the Court's own reasoning; the rest are FACTS/HEADER recitals — the known base-rate problem, now quantified)

## Duplicate-document rate in top-k
- **0.000** (MMR active)

## Precision@6 (strict criterion, judged on full chunk text)
- overall: **0.451** (n=144)
- by query language: {'de': 0.594, 'en': 0.167}
- by jurisdiction: {'AT (OGH)': 0.606, 'CH': 0.587, 'ECHR': 0.167}
- ECHR hits by section: {'FACTS': 0.0, 'HEADER': 0.0, 'LAW': 0.727, 'OPERATIVE': 0.0, 'PROCEDURE': 0.0} — LAW-section hits are precise, everything else is noise: the LAW-share problem IS the ECHR precision problem.

## Reading
- The jurisdiction-mix table is the honest RQ4 retrieval claim: German queries retrieving from AT/CH corpora (and English from ECHR) shows the shared multilingual embedding space routes by content, not by accident of language. Cross-language hits are not errors per se — e5 is multilingual — but a German query answered *only* by English chunks would mean the German corpora add no retrieval value.
- Annotation protocol (strict criterion): relevant=1 ONLY if the chunk states the deciding court's OWN rule/reasoning on the query's legal question; facts recitals, quoted statutes/domestic law, party submissions, headnotes/captions, operative paragraphs and procedural narration = 0, regardless of topical overlap. Judged on the full chunk text, not the truncated CSV snippet. Labels drafted with LLM assistance under this written criterion and reviewed by the author — a scoped, reproducible measurement, not an IR benchmark.
