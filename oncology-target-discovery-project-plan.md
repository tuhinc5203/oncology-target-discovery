# Oncology Target Discovery Project — Full Build Plan
### (DepMap + TCGA + GTEx target identification & prioritization pipeline)

**Goal:** Build a computational pipeline that identifies and ranks candidate cancer therapeutic targets by integrating three public data sources: gene essentiality (DepMap CRISPR screens), tumor vs. normal expression (TCGA + GTEx), and clinical relevance (survival analysis). This is the in-silico front end of the exact workflow you supported at the bench at Oxford Biotherapeutics — there, you validated candidate targets after they'd been identified; here, you're building the tool that helps identify them in the first place.

**Current cancer focus:** Triple-negative breast cancer (TNBC).

**Why this project specifically:** Target identification/prioritization is a core computational biology function at every major oncology-focused pharma (Genentech, Amgen, Gilead, AbbVie all have dedicated target discovery groups). Because you've done wet-lab target validation, you're uniquely positioned to build this well — you know what actually makes a target credible (expression pattern, essentiality, safety window, druggability), not just what makes a statistically significant hit.

**Total estimated time:** 5–6 weeks, roughly 5–8 hours/week alongside coursework — same pacing as the ADMET project, so the two can run back-to-back or be alternated.

---

## Before you start: tools and accounts

| Tool | Purpose | Notes |
|---|---|---|
| VS Code + Claude Code extension | Editor + AI coding assistant | Same setup as your ADMET project — reuse the environment habits from that plan |
| Python 3.10+ (conda env) | Base language | `conda create -n target-discovery python=3.10` |
| pandas, numpy, scipy | Data handling + statistics (t-tests, effect sizes) | Standard |
| matplotlib / seaborn | Plotting | Standard |
| `lifelines` | Survival analysis (Kaplan-Meier, Cox regression) on TCGA clinical data | `pip install lifelines` |
| DepMap Portal account | Download CRISPR gene-effect and cell line data | Free, [depmap.org/portal](https://depmap.org/portal) |
| UCSC Xena Browser | Simplest way to get pre-processed TCGA expression + clinical data | Free, no account needed for bulk downloads, [xenabrowser.net](https://xenabrowser.net) |
| GTEx Portal | Normal tissue baseline expression | Free, bulk download, [gtexportal.org](https://gtexportal.org) |
| Human Protein Atlas | Protein class / druggability annotations (optional but valuable) | Free, [proteinatlas.org](https://proteinatlas.org) |
| GitHub account | Hosting the finished project | You already have this from the ADMET project |
| (Optional, later) Streamlit | Interactive target-explorer dashboard | `pip install streamlit` |

No deep learning needed here either — this project is about statistical rigor and biological reasoning across integrated datasets, which is arguably a *better* showcase of judgment than another modeling exercise.

---

## Week 0 (2–3 days): Setup + choose your cancer focus

**Steps:**
1. In VS Code, create the project folder (`oncology-target-discovery`), open it, set up the conda environment as above, and select it as your Jupyter kernel — same process as the ADMET project.
2. Create a `CLAUDE.md` in the project root describing the goal and current status, and initialize/connect a GitHub repo.
3. **Choose triple-negative breast cancer (TNBC) as the focus.** This matters — a target discovery pipeline needs a defined biological question, not "all of cancer." TNBC is a strong fit because:
   - You have prior experience working on TNBC targets at Oxford Biotherapeutics, giving you relevant biological and target-validation context without relying on proprietary information.
   - TNBC is a common breast cancer subtype with substantial public data and an important unmet-need and drug-development context.
   - The scope is specific enough for a credible target-discovery question while still supporting useful DepMap, TCGA, and GTEx analyses.
   - Record this decision in the project notes, including the distinction between public-domain rationale and any proprietary work history.
4. Register for DepMap Portal access and download the current release's **CRISPR gene effect (Chronos) scores** and **cell line sample info** files. Familiarize yourself with the file structure in a notebook.

**Deliverable:** environment set up, cancer type chosen and justified in a short markdown note, DepMap files downloaded.

*Claude Code tip: once you've picked your cancer type, have Claude Code help you write a small data-loading utility module (`data_utils.py`) with functions to load and lightly clean each data source — you'll reuse these every week.*

---

## Week 1: Data acquisition + EDA across all three sources

**Steps:**
1. **DepMap**: load the CRISPR gene-effect matrix (genes × cell lines, values are essentiality scores — more negative means more essential). Identify breast cancer cell lines and use available molecular subtype annotations or a documented TNBC cell-line mapping to define the TNBC analysis set.
2. **TCGA**: via UCSC Xena, download the breast cancer (`TCGA-BRCA`) gene expression matrix and the matching clinical/phenotype file (includes survival data — vital status, days to death/follow-up). Use the available molecular subtype annotations to isolate or sensitivity-test the TNBC cohort rather than treating all breast tumors as TNBC.
3. **GTEx**: download the bulk median TPM-by-tissue file — this becomes your "normal tissue" baseline for filtering out targets that are also highly expressed in healthy tissue (a safety/therapeutic-window concern, exactly the kind of judgment a target validation scientist applies).
4. Do basic EDA on each: dimensions, missingness, distribution of key values. Write a markdown note per dataset explaining what it captures biologically and why it's part of your pipeline — this becomes README material later, same as the ADMET project.

**Deliverable:** all three datasets loaded, cleaned, and explored in notebooks; cell lines mapped to your cancer type. Commit to GitHub.

---

## Week 2: Selective essentiality analysis (DepMap)

**What you're doing:** identifying genes that are *selectively* essential in your cancer type — i.e., knocking them out kills your cancer-type cell lines specifically, more than it kills other cancer types. This is the "does the cancer depend on this gene" half of target identification.

**Steps:**
1. Compute the mean/median dependency score for every gene within your cancer-type cell lines vs. all other cell lines in DepMap.
2. Use a statistical test (Mann-Whitney U or t-test, with multiple-testing correction — e.g., Benjamini-Hochberg FDR) to identify genes with significantly stronger dependency in your cancer type.
3. Rank candidates by effect size and significance. Produce a shortlist of your top ~30–50 selectively essential genes.
4. Sanity-check a few known targets in your cancer type against your results — do you recover genes already known to be important in this disease? This is a credibility check worth explicitly writing up: "my pipeline recovers known biology X, which validates the approach before trusting novel candidates."

**Deliverable:** ranked list of selectively essential candidate genes for your cancer type, with the sanity-check discussion. Commit to GitHub.

*Claude Code tip: the statistical testing loop across thousands of genes is a good candidate to hand off — describe exactly what comparison and correction method you want, then review the output logic yourself so you can explain the statistics choices in an interview.*

---

## Week 3: Tumor-selectivity and safety filtering (TCGA + GTEx)

**What you're doing:** essentiality alone isn't enough — a good therapeutic target should also be **overexpressed in tumor relative to normal tissue** (so a drug can hit the tumor without excessive off-target damage) and **not essential/highly expressed in critical normal tissues**.

**Steps:**
1. For your shortlist from Week 2, compute differential expression: tumor samples (TCGA) vs. matched normal tissue (TCGA has some matched-normal samples; supplement with GTEx for tissue-general baseline).
2. Filter or re-rank your shortlist: prioritize genes that are both selectively essential *and* tumor-overexpressed relative to normal tissue.
3. Flag genes that are highly expressed in normal tissues associated with known dose-limiting toxicities (e.g., high expression in heart, liver, or bone marrow tissue in GTEx would be a caution flag) — this is where your pathology/toxicology intuition from real target validation work directly informs the analysis.
4. (Optional, high-value) Pull **protein class annotations from the Human Protein Atlas** for your remaining candidates — is it a cell-surface receptor, kinase, secreted protein? These classes are generally more tractable for drug/antibody development, which is a meaningful signal for a pharma reviewer.

**Deliverable:** a filtered, re-ranked candidate list with tumor-selectivity and normal-tissue safety annotations. Commit to GitHub.

---

## Week 4: Clinical relevance (survival analysis) + composite scoring

**What you're doing:** does expression of your candidate targets actually correlate with patient outcomes? This is the step that moves a target from "statistically interesting" to "clinically plausible" — and it's also the most impressive technical addition to the project.

**Steps:**
1. Using `lifelines`, run Kaplan-Meier survival analysis for your top candidates: split TCGA patients into high vs. low expression groups (e.g., median split) for each gene and compare survival curves.
2. Run a Cox proportional hazards model for your top few candidates, optionally adjusting for basic clinical covariates (age, stage) if available in the clinical file.
3. Build a **composite prioritization score** combining: essentiality effect size (Week 2) + tumor-selectivity magnitude (Week 3) + survival association strength (this week) + optionally a druggability flag (protein class). Weight and justify your scoring choices explicitly in a written note — this is a judgment call, and being able to defend it is exactly the skill being tested.
4. Produce a final ranked table of your top 5–10 candidate targets.

**Deliverable:** survival analysis for top candidates, composite scoring methodology, final ranked target list. Commit to GitHub.

*Claude Code tip: have it help you build the Kaplan-Meier plotting loop across multiple genes efficiently, but write the scoring-weight justification yourself in your own words — that section is what a reviewer will actually read closely.*

---

## Week 5: Deep dive + documentation + polish

**Steps:**
1. Pick your **top 1–2 candidate targets** and do a short "case study" write-up: what is known about this gene/protein in the literature, is it already a drug target elsewhere, what would the next experimental step be (tying back to your actual bench skills — e.g., "next step would be IHC validation of protein expression across a tissue microarray," which you can speak to from direct experience).
2. Write the full README: motivation, data sources, methodology (essentiality → tumor selectivity → safety filtering → survival analysis → composite score), results table, and the case study.
3. Add a results visualization (e.g., a summary plot showing your top candidates across all scoring dimensions) as an image in the README.
4. Pin your environment (`environment.yml`), clean up notebooks with markdown explanations between cells.
5. (Optional) Build a simple Streamlit dashboard where a user can select a gene and see its essentiality, expression, and survival profile — a nice interactive layer if you have the time.

**Deliverable:** polished, documented, reproducible GitHub repo with a clear narrative case study.

---

## Timeline summary

| Week | Focus | Hours (approx.) |
|---|---|---|
| 0 | Setup + choose cancer focus | 2–4 |
| 1 | Data acquisition + EDA (DepMap, TCGA, GTEx) | 6–8 |
| 2 | Selective essentiality analysis | 6–8 |
| 3 | Tumor-selectivity + safety filtering | 5–7 |
| 4 | Survival analysis + composite scoring | 6–8 |
| 5 | Case study + documentation + polish | 5–7 |
| **Total** | | **~30–42 hours over 5–6 weeks** |

---

## How to talk about this on your resume / in interviews

**Resume bullet (example):**
> Built a computational oncology target discovery pipeline integrating DepMap CRISPR dependency screens, TCGA/GTEx differential expression, and survival analysis to identify and rank candidate therapeutic targets in [cancer type]; validated pipeline against known biology and produced a scored candidate shortlist with a detailed case study.

**In an interview, be ready to explain:**
- Why you chose selective essentiality + tumor-overexpression + normal-tissue safety as your three filtering criteria — and be able to connect this explicitly to your bench experience validating targets at Oxford Biotherapeutics.
- How you weighted your composite score, and what you'd change with more data (e.g., proteomics, single-cell expression for tumor microenvironment context).
- The sanity-check step (recovering known biology) — this is a strong signal of scientific rigor that many candidates skip.
- What the natural next experimental step would be for your top candidate — this is where you can speak fluently as someone who has actually run IHC validation, which almost no purely computational candidate can do.

This project and the ADMET project together tell a coherent story: one shows you can build predictive models for compound developability (chemistry side), the other shows you can do target identification and validation computationally (biology side) — bookending the drug discovery pipeline with your own work, on top of the domain credibility you already have from real bench experience.
