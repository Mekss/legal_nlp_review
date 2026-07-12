# Feasibility Analysis: Web Scraping & NLP for Parental Alienation Discourse

**Master's Thesis — Data Collection & Methodology Report**

---

## 1. Research Context

This thesis investigates how the concepts of *parental alienation* (Entfremdung) and *child welfare* (Kindeswohl) are framed across different types of discourse — legal, political, and public — with a focus on Austria and a comparative international dimension.

The core idea is that the same concepts are discussed in fundamentally different ways depending on who is speaking: courts use precise legal language anchored to specific statutes, international human rights bodies frame them as rights violations, and the public expresses them as personal grievances. By applying consistent NLP methods across these discourse levels, we can surface these framing differences systematically.

---

## 2. Data Sources: What We Collected and Why

### 2.1 Austrian Court Decisions — RIS OGD API v2.6

**Source:** Official Austrian Legal Information System, `data.bka.gv.at/ris/api/v2.6/`

**What we collected:** 36 Rechtssätze (legal principle summaries) from the OGH (Supreme Court) matching the keyword "Entfremdung" and related terms.

**Why Rechtssätze, not full decisions:** Each Rechtssatz is a court-distilled legal principle — 2–5 sentences of authoritative legal language. They are *not* abbreviated versions of decisions; they are a distinct document type in the Austrian legal system, designed to capture the binding legal takeaway. A single Rechtssatz references all cases that applied the principle (one of ours cites 79 cases spanning 1978–2025). They also contain T-variants (refinements added by later courts) and Beisätze (judicial annotations), which encode how the principle evolved over decades.

For NLP analysis, this is arguably better data than full decision texts. Full decisions contain pages of procedural history, party names, and cost rulings — noise that dilutes the signal. Rechtssätze are pre-filtered to the legal substance.

**Technical details:**
- API is a free REST endpoint, no authentication needed
- Returns structured JSON with rich metadata (ECLI, norms, court, date, legal area)
- Pagination is broken (the `Seite` parameter is ignored) — workaround: year-by-year date-range windowing
- Page size is fixed at 20 regardless of the `Seitengroesse` parameter
- Full text must be fetched separately from content URLs (HTML/XML/PDF available)
- Single results return as a dict, not a list — parser must handle both

**Status:** ✅ Collected and operational. Notebook: `ris_ogd_api_scraper_v2.ipynb`

---

### 2.2 ECHR Case Law — echr_extractor

**Source:** European Court of Human Rights (HUDOC database) via the `echr_extractor` Python library.

**What we collected:** Cases matching keywords "parental alienation," "child welfare," "best interests of the child," "contact rights," "custody AND alienation," "Kindeswohl," and "Entfremdung" — across all Convention articles (no Article 8 filter, to avoid pre-selecting results).

**Why ECHR:** Austrian parental alienation cases sometimes reach Strasbourg when a parent claims the state failed to protect their right to family life. The ECHR provides the international human rights layer of our analysis. Importantly, many Austrian RIS decisions already contain ECLI references to ECHR case law, creating a traceable chain between domestic and international jurisprudence.

**Why no article filter:** While Article 8 (Right to Private and Family Life) is the obvious match, parental alienation also appears in Article 3 cases (inhuman treatment), Article 6 cases (fair trial in custody proceedings), and Article 14 cases (discrimination). Dropping the filter lets the data tell us which articles come up — itself a finding.

**Technical details:**
- Library: `echr_extractor` (pip install echr-extractor)
- `get_echr_extra()` returns metadata + full judgment texts
- Critical bug: library uses 1-second HTTP timeout internally (`ECHR_html_downloader.py:68`), causing silent download failures — fixed by manually patching to 30 seconds in `.venv`
- Full texts are in English
- Rich metadata includes: respondent country, articles violated, importance ranking, cited case law (SCL field — a citation network for free)

**Status:** ✅ Collected. Script: `echr_scraper.py`

---

### 2.3 German Court Decisions — Open Legal Data

**Source:** `de.openlegaldata.io`, a free nonprofit platform with 100k+ German court decisions and a documented REST API.

**What we collected:** 107 decisions (2018–2025) matching keywords including Entfremdung, Kindeswohl, Kindeswohlgefährdung, Sorgerechtsentzug, Umgangsrecht, PAS, and elterliche Entfremdung.

**Why Germany:** Germany shares the civil law tradition and largely overlapping German legal terminology with Austria, making direct linguistic comparison possible. However, there are notable terminology differences: "Umgangsrecht" (DE) vs. "Kontaktrecht" (AT) for visitation, "Sorgerecht" (DE) vs. "Obsorge" (AT) for custody.

**Critical finding — false positives:** "Entfremdung" in German case law frequently appears in non-family-law contexts (inheritance disputes, property law). A family law relevance filter (co-occurrence with terms like "Kindeswohl," "Sorgerecht," "Elternteil") is mandatory. Similarly, "PAS" matches substrings in unrelated words. Of 107 raw results, the relevant subset after filtering is smaller — the false positive rate itself is a methodological finding to document.

**Limitation:** German courts publish far fewer decisions than Austrian RIS — only ~1.4% of all cases. Lower courts (where most custody disputes happen) are largely absent. Results are biased toward higher courts (OLG, BGH).

**Status:** ✅ Collected. Notebook: `src/open_legal_data_germany.ipynb`

---

### 2.4 Swiss Court Decisions — entscheidsuche.ch

**Source:** entscheidsuche.ch, an open platform covering 350k+ decisions from all Swiss courts (federal + all 26 cantons), with an Elasticsearch search API.

**What we are collecting:** Decisions matching the same German-language keywords, filtered to German-language decisions only.

**Why Switzerland:** Completes the DACH comparison (Germany-Austria-Switzerland). Switzerland uses distinct terminology: "Obhut" (CH) vs. "Obsorge" (AT) for custody, "elterliche Sorge" (CH) for parental authority. Unlike Germany, Swiss cantonal courts publish more broadly, and entscheidsuche.ch aggregates them.

**Technical details:**
- Elasticsearch endpoint: `https://entscheidsuche.ch/_search.php`
- Query using Elasticsearch DSL (POST with JSON body)
- No API key needed
- Documents have JSON metadata + separate HTML files for full text
- Full text must be fetched from `https://entscheidsuche.ch/docs/{path}`
- The API maintainer explicitly permits academic use; asks for attribution

**Status:** 🔜 In progress. Notebook: `src/swiss_court_decisions.ipynb`

---

### 2.5 Reddit — Public Discourse

**Source:** Reddit, German-language subreddits.

**What we collected:** Posts and comments from relevant subreddits (parenting, legal advice, relationship-focused communities) containing our keywords.

**Why Reddit:** Provides the public discourse layer. Reddit is pseudonymous and free-form — people describe parental alienation experiences in their own words, unconstrained by legal frameworks. The contrast with how courts use the same terminology is the core analytical tension of the thesis.

**Status:** ✅ Collected. Notebook: `DACH_SingleParent_Reddit_Analysis (3).ipynb`

---

## 3. Sources Evaluated and Rejected

### 3.1 Sweden
**Rejected: No accessible data.** Swedish court decisions are not systematically published online. Only a small selection of Supreme Court precedents exists on domstol.se, with no API and no bulk access. District courts (where family law cases are decided) publish nothing publicly. The language barrier (Swedish) would require a separate NLP pipeline and keyword vocabulary.

### 3.2 Australia, US, UK
**Rejected: Incompatible legal systems.** All three use common law (case precedent), not civil law. Legal reasoning structure, terminology, and document formats are fundamentally different from the DACH civil law tradition. Australia's AustLII has rich data (including a dedicated Family Court database from 1982+) but no API for bulk access. Adding these would break the methodological coherence of a German-language civil law comparison.

### 3.3 Twitter/X, Facebook
**Rejected: API restrictions and ethics.** Twitter's API is now paid and heavily restricted. Facebook groups on parental alienation exist but are semi-private, and scraping raises consent issues for a thesis.

### 3.4 NeuRIS (Germany)
**Rejected: Not yet available.** The new German legal information system (replacing Gesetze-im-Internet, Rechtsprechung-im-Internet) is still under development. Once launched, it would be the authoritative source for German federal decisions. For now, Open Legal Data serves as the best available alternative.

### 3.5 OpenJur (Germany)
**Not used but viable as supplement.** Has 600k+ decisions (vs. 100k on Open Legal Data) but the API is less documented and more aimed at practitioners than researchers. Could supplement if more German data is needed.

---

## 4. Cross-Cutting Methodology: KWIC (Keyword in Context)

Across all sources, we apply a consistent **KWIC extraction** with a 400-character window (200 characters before and after each keyword occurrence). This produces comparable text snippets regardless of document length or structure.

KWIC serves as the unifying analytical method because it normalizes across radically different document types: a 3-sentence Rechtssatz, a 50-page ECHR judgment, and a 200-word Reddit post all produce the same format — a keyword surrounded by its immediate context. This enables direct comparison of how the same concept is framed across discourse levels.

For Austrian Rechtssätze specifically, the T-variants and Beisätze function as a form of pre-made KWIC — the court system itself has already extracted the key principle in context. This is a complementary perspective: researcher-defined KWIC vs. institutionally-defined context.

---

## 5. Data Summary

| Source | Country | Discourse Level | Language | Documents | Full Text | Status |
|--------|---------|----------------|----------|-----------|-----------|--------|
| RIS OGD API | Austria | Judicial (domestic) | German | 36 Rechtssätze | ✅ | Collected |
| Open Legal Data | Germany | Judicial (domestic) | German | 107 cases | ✅ | Collected |
| entscheidsuche.ch | Switzerland | Judicial (domestic) | German | TBD | ✅ | In progress |
| ECHR / HUDOC | International | Judicial (supranational) | English | ~50–200 | ✅ | Collected |
| Reddit | DACH region | Public discourse | German | TBD | ✅ | Collected |

---

## 6. Proposed Research Questions

### Primary Research Question

**"How does the framing of parental alienation (Entfremdung) and child welfare (Kindeswohl) differ across Austrian legal decisions, DACH comparative case law, ECHR jurisprudence, and public online discourse?"**

This is answerable with the data we have, uses all five sources, and naturally structures the thesis around discourse levels rather than countries.

### Supporting Questions

**RQ1 (Legal framing):** Which legal norms do Austrian courts anchor "Entfremdung" to, and how has the judicial framing evolved over time (1978–2025)?
→ *Answerable with:* RIS Rechtssätze metadata (normen, T-variants, citation timelines)

**RQ2 (Cross-jurisdictional comparison):** Do German and Swiss courts use "Entfremdung" in the same legal contexts as Austrian courts, or does terminology diverge across jurisdictions?
→ *Answerable with:* KWIC comparison across RIS, Open Legal Data, and entscheidsuche.ch

**RQ3 (International framing):** How does the ECHR frame parental alienation compared to domestic DACH courts — as a rights violation, procedural failure, or child welfare issue?
→ *Answerable with:* ECHR metadata (articles violated, conclusion field) + KWIC on full texts

**RQ4 (Public vs. legal discourse):** Do members of the public on Reddit frame "Entfremdung" and "Kindeswohl" differently from how courts use these terms — and if so, how?
→ *Answerable with:* KWIC comparison between Reddit and legal sources, topic modeling

---

## 7. Proposed Methods

### 7.1 Keyword-in-Context (KWIC) Analysis
Applied uniformly across all five corpora. 400-character window around each keyword occurrence. Produces the primary dataset for comparative analysis. Can be analyzed both qualitatively (reading contexts) and quantitatively (co-occurrence patterns).

### 7.2 Keyword Co-occurrence / Collocation Analysis
For each source, measure which words systematically appear near our keywords. For example: does "Entfremdung" co-occur with "Gefährdung" (endangerment) in courts but with "Narzissmus" (narcissism) on Reddit? This reveals framing differences. Implemented with spaCy or NLTK on German text; no model training needed.

### 7.3 Topic Modeling (BERTopic)
Apply BERTopic with a multilingual sentence transformer (`paraphrase-multilingual-MiniLM-L12-v2`) to identify thematic clusters within each corpus and across corpora. Free, pre-trained, no fine-tuning needed. Works on both German and English text.

### 7.4 Temporal Analysis
Using the citation timelines from RIS Rechtssätze (Geschaeftszahl lists with year-encoded case numbers), ECHR judgment dates, and Reddit post timestamps: how does the frequency and framing of parental alienation discourse change over time? Do courts lead or follow public discourse?

### 7.5 Legal Citation Network Analysis
RIS Rechtssätze contain the norms cited (e.g., "§ 180 ABGB") and all cases that applied each principle. ECHR cases contain the SCL field listing cited precedent. This allows mapping which legal principles cluster around parental alienation without NLP — purely from structured metadata.

### 7.6 Family Law Relevance Filtering
A methodological contribution: documenting false positive rates across sources. "Entfremdung" in German case law appears in inheritance, property, and criminal contexts. The filtering approach (co-occurrence with family law terms) and the false positive rates themselves are part of the analysis.

---

## 8. Tools and Infrastructure

| Tool | Purpose | Cost |
|------|---------|------|
| Python 3.9+ with Jupyter | All data collection and analysis | Free |
| requests + BeautifulSoup | API calls and HTML parsing | Free |
| pandas | Data wrangling | Free |
| spaCy (de_core_news_sm) | German tokenization, NER | Free |
| BERTopic + sentence-transformers | Topic modeling | Free (pre-trained) |
| matplotlib | Visualization | Free |
| echr_extractor | ECHR data collection | Free |

All models are pre-trained and free. No fine-tuning, no paid APIs, no GPU required.

---

## 9. Limitations

1. **RIS pagination is broken.** The API ignores the `Seite` parameter. Year-by-year windowing works but any single year with >20 results will be incomplete.

2. **German publication gap.** Only ~1.4% of German court decisions are published. Family court (Amtsgericht) decisions are almost entirely absent. Results are biased toward appellate courts.

3. **"Entfremdung" is polysemous.** The word means "estrangement" broadly, not just parental alienation. Every corpus requires a relevance filter, which introduces subjectivity.

4. **ECHR is English-only.** Cross-linguistic comparison between German legal texts and English ECHR judgments requires careful methodology — the same concept may be expressed with different connotations.

5. **Reddit data is self-selected.** Users who post about parental alienation are not representative of the general public.

6. **Swiss data depends on API stability.** entscheidsuche.ch is a nonprofit project; the Elasticsearch endpoint may change.
