# Thesis Ideas — Brainstorming

**Context:** Data available from RIS (Austria, full texts + Rechtssätze), Open Legal Data (Germany, full decision texts), entscheidsuche.ch (Switzerland, full texts), ECHR (full texts), Reddit (DACH public discourse). All German-language legal sources + English ECHR and Reddit. KWIC extraction pipeline operational across all sources.

---

## Research Questions 
### Framing & Discourse

1. How does the framing of "Entfremdung" differ across Austrian courts, German courts, Swiss courts, ECHR, and public Reddit discourse? Which terminilogies appear in the context?
4. Do courts frame alienation as reversible or irreversible harm, and does this differ by jurisdiction?
5. Who gets blamed for alienation in legal vs public discourse — the mother, the father, the system, or the alienating parent without gender?
6. Does Reddit discourse asnticipate or follow judicial developments in parental alienation?
8. Is there a gap between how courts define "Kindeswohlgefährdung" and how the public understands it?
9. Do Austrian Rechtssatz T-variants show a measurable shift in judicial language about alienation over the past 40 years?

## Research Questions
 
### Comparative (Legal)

1. Which DACH country's courts use "Entfremdung" most frequently in family law contexts, and what does the false positive rate reveal about legal terminology precision?
16. Which ECHR respondent countries are most frequently found in violation for failing to prevent parental alienation?

## Research Questions 
### Temporal

1. When does "Entfremdung" first appear in Austrian case law as a family law concept vs general estrangement?
20. Does the frequency of "Kindeswohl" in court decisions increase after the KindNamRÄG 2013 reform?
21. How has the ECHR's language on parental contact evolved from early cases (1990s) to recent judgments (2020s)?

## Research Questions 
### Public Discourse

1. What emotional framing dominates Reddit discussions of Entfremdung — anger, helplessness, advocacy, or resignation?
28. How do gendered narratives about alienation differ between Reddit and court decisions? 
29. Do German-speaking Reddit communities discuss alienation differently from English-speaking ones?

## Methods

1. KWIC co-occurrence analysis: compare which words appear within 400 characters of "Entfremdung" across all sources to quantify framing differences.
32. BERTopic with multilingual sentence transformer on all KWIC contexts to discover latent thematic clusters across sources.
33. Temporal citation network from Rechtssatz Geschaeftszahl fields — map how frequently each legal principle is cited per year.
35. False positive classification as a methodological contribution — document and quantify how "Entfremdung" distributes across legal domains (family, inheritance, property, tax, criminal).
39. Document similarity clustering: embed all KWIC contexts with sentence-transformers and visualize source separation in 2D (UMAP).

## Scope & Framing

1. Frame thesis as "discourse analysis" — comparing institutional vs public (Reddit based) framing of a contested concept.
43. Frame thesis as "comparative law" — how DACH jurisdictions handle the same family law concept differently (how things are worded).
44. Frame thesis as "data engineering" — building a reproducible pipeline for cross-jurisdictional legal text analysis.
48. Limit scope to post-2013 (KindNamRÄG reform) for all AT sources. Or create pre and post split for Austria.
50. Present the false positive filtering methodology as a standalone contribution: "A replicable pipeline for extracting domain-specific legal concepts from general-purpose court databases."


## Current keywords:
### German keywords
KEYWORDS_DE = [
    "Alleinerziehende",
    "Alleinerziehender",
    "Einelternfamilie",
    "alleinerziehend",
    "Alleinerziehenden",
    "Alleinerzieherin",
    "Sozialmutter",
    "Solovater",
    "Solomutter",
]

### English keywords
KEYWORDS_EN = [
    "single parent",
    "single mother",
    "single father",
    "single mom",
    "single dad",
    "lone parent",
]


## New keywords
* Bindungstoleranz
* Loyalitätskonflikt
* Kontaktverweigerung
* Beeinflussung
* Kontaktabbruch
* Einelternfamilie
* Residenzmodell
* Hauptbetreuungsperson
* Besuchsvater/mutter
* Obsorge
* Kontaktrecht


#### more things
* contact - how much time children are supposed to spend how much time in which age
* how good can we use AI models (provide references to original src when asnwering questions)
* precision (maybe not recall)
* CUSTODY
* married if it makes a difference
* language/ethnicity
* how many children with whih parent (m/f?)
* why cases end up at highest court?
* cases vs population
* communication between parents (vs age of children)
* extended family
