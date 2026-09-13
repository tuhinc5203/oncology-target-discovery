# Oncology Target Discovery Notes

## Project in one sentence

Build a reproducible public-data pipeline to identify and prioritize potential therapeutic targets in triple-negative breast cancer (TNBC).

## Why TNBC?

I chose TNBC because I have previously worked on TNBC targets at Oxford Biotherapeutics, giving me useful biological and target-validation context. TNBC is also a common breast cancer subtype with substantial public data and an important unmet need.

The project will use only public data and public-domain reasoning. It will not include proprietary targets, results, methods, or confidential information from previous work.

## How the project works

1. **Dependency:** DepMap CRISPR screens show which genes TNBC cells depend on for survival.
2. **Tumor selectivity:** TCGA and GTEx show whether candidate genes are more expressed in tumor than in normal tissue.
3. **Clinical relevance:** TCGA clinical data show whether candidate expression is associated with patient outcomes.
4. **Prioritization:** These signals are combined with safety and, optionally, druggability information to produce a ranked shortlist.

## Week 0: Setup and scope

- [x] Set up the Python environment and Jupyter kernel.
- [x] Create the project repository.
- [x] Choose TNBC as the cancer focus.
- [x] Record the TNBC rationale.
- [ ] Register for DepMap access.
- [ ] Download the current Chronos gene-effect and cell-line metadata files.
- [ ] Inspect the DepMap files and record their release/version.

**Week 0 outcome:** The biological question is defined: which genes are selectively important in TNBC and plausible as therapeutic targets?

## Week 1: Collect data and understand it

- [ ] Load and lightly clean the DepMap gene-effect matrix.
- [ ] Define the TNBC cell-line set using subtype annotations or a documented mapping.
- [ ] Download TCGA-BRCA expression and clinical data.
- [ ] Use molecular subtype annotations rather than treating every breast tumor as TNBC.
- [ ] Download GTEx median expression by tissue.
- [ ] Record dimensions, missingness, and distributions.
- [ ] Write a short explanation of what each dataset contributes.

**Week 1 outcome:** Clean, understood datasets and a defensible definition of the TNBC analysis groups.

## Week 2: Find selectively essential genes

- [ ] Compare gene dependency in TNBC cells with other cell lines.
- [ ] Use an appropriate statistical test and correct for multiple comparisons.
- [ ] Rank genes by dependency effect and statistical evidence.
- [ ] Create a shortlist of approximately 30–50 candidates.
- [ ] Check whether the analysis recovers known TNBC biology.

**Week 2 outcome:** A ranked list of genes that TNBC cells appear to depend on preferentially.

## Week 3: Check tumor selectivity and safety

- [ ] Compare candidate expression in TNBC tumors with normal tissue baselines.
- [ ] Prioritize genes that are both selectively essential and tumor-enriched.
- [ ] Flag expression in critical normal tissues as a potential safety concern.
- [ ] Optionally add Human Protein Atlas protein-class and druggability annotations.

**Week 3 outcome:** A smaller list with evidence for tumor selectivity and an initial safety assessment.

## Week 4: Test clinical relevance and score candidates

- [ ] Run Kaplan-Meier analysis for the leading candidates.
- [ ] Run Cox models for the strongest candidates.
- [ ] Define and explain the composite score.
- [ ] Combine dependency, tumor selectivity, survival, safety, and optional druggability signals.
- [ ] Produce a final ranked list of 5–10 targets.

**Week 4 outcome:** A ranked target list supported by multiple independent lines of evidence.

## Week 5: Explain and polish the result

- [ ] Select one or two leading targets for a literature and druggability case study.
- [ ] Describe the next experimental validation step.
- [ ] Write the README using the project story and results recorded here.
- [ ] Add a summary visualization.
- [ ] Pin the environment and clean the notebooks.
- [ ] Build the optional Streamlit explorer if time allows.

**Week 5 outcome:** A reproducible portfolio project with a clear scientific narrative and defensible conclusions.

## Results and decisions log

Add dated notes here as the project develops:

- **Date:**
- **Decision or result:**
- **Why it matters:**
- **Next action:**

- **Date:** 2026-09-13
- **Decision or result:** Created the `target-discovery` conda environment (Python 3.10) with pandas, numpy, scipy, matplotlib, seaborn, lifelines, and jupyter/ipykernel; registered the Jupyter kernel. Initialized the local git repository (`main` branch) with a `.gitignore`, `environment.yml`, and a `data/raw/` vs `data/processed/` folder layout (`data/raw/{depmap,tcga,gtex,hpa}`, plus `notebooks/` and `src/`). First commit made.
- **Why it matters:** Completes the environment and repository setup items from the Week 0 checklist so analysis code has somewhere reproducible to live.
- **Next action:** Register for DepMap Portal access and download the current release's CRISPR gene-effect (Chronos) and cell-line metadata files — this step needs to happen in your browser (see open item below).

- **Date:** 2026-09-13
- **Decision or result:** Checked whether DepMap files could be fetched programmatically. The DepMap portal now sits behind a Cloudflare bot-verification/login gate (confirmed via direct API request to `/portal/api/download/files`, which returned a verification page, not data). As of the 25Q2 release, DepMap also no longer bulk-publishes to Figshare; the two supported paths are: (1) the portal's "Custom Downloads" tab, or (2) fetching `https://depmap.org/portal/api/download/files` from a logged-in browser session to get a CSV of signed, time-limited download URLs.
- **Why it matters:** This step cannot be automated from here — it requires your own DepMap account and browser session.
- **Next action:** You need to: (1) create/log into a DepMap Portal account at depmap.org/portal if you haven't already, (2) go to the Data page for the current public release, (3) download `CRISPRGeneEffect.csv` (Chronos scores) and the cell line metadata file (`Model.csv`), and (4) drop them into `data/raw/depmap/`. Tell me once they're there and I'll inspect the schema and record the release version.
