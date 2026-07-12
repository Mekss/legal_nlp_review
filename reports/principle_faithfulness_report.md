# Principle faithfulness report (embedding-based, topic-agnostic)

- n = **29** Rechtssaetze with indexed applying decisions.
- faithfulness (max cos, principle -> own applying decisions): median **0.896**
- baseline (max cos -> equal random sample of other decisions): median **0.863**
- specificity margin: median **0.028**; **26/29** principles are closer to their own case-law than to random family-law decisions.
- figure: `figures/ris_principle_faithfulness.png`

## Reading
- High faithfulness with a positive margin supports treating Rechtssaetze as **semantic surrogates** for their case-law in retrieval (why the `principle` genre scores highest precision) — measured, not assumed.
- Near-zero margins flag principles whose corpus decisions discuss them only in passing — retrieval hits on such principles cite the RS, not the reasoning.
- Topic-agnostic: RS-decision links + cached vectors only; corpus-relative (applying decisions outside the keyword corpus are invisible).
