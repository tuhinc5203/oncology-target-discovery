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

## Why each data source matters

### DepMap (CRISPR dependency screens)

DepMap runs genome-wide CRISPR knockout screens across hundreds of cancer cell lines and reports a "gene effect" score (via the Chronos algorithm) for every gene in every cell line — essentially, how much that cell line's growth/viability drops when the gene is knocked out. More negative means more essential to that cell line's survival. This is the "does the cancer actually depend on this gene" signal, and it's the genome-wide, in-silico analog of exactly what target validation does at the bench one gene at a time.

### TCGA-BRCA (tumor expression + clinical outcomes)

The Cancer Genome Atlas's breast cancer cohort provides RNA-seq expression and clinical/survival data from real patient tumors. This answers two different questions from DepMap: is a gene that looks essential in TNBC cell lines actually turned up in real TNBC tumors (not just a cell-culture artifact)? And do patients whose tumors express it highly have worse outcomes? Together these move a candidate from "cell-line finding" toward "clinically plausible."

### GTEx (normal tissue baseline)

The Genotype-Tissue Expression project profiles gene expression across dozens of normal (non-cancerous) human tissues. This is the safety/therapeutic-window check: a gene can be essential *and* tumor-overexpressed and still be a bad target if it's also highly expressed in the heart, liver, or bone marrow — a drug hitting it would likely cause dose-limiting toxicity before it could work on the tumor. This is the same kind of judgment a target-validation scientist applies before recommending a target for further investment.

### Human Protein Atlas (optional — druggability context)

Protein-class annotations (kinase, cell-surface receptor, secreted protein, etc.), planned as an optional Week 3 addition. Used to flag which surviving candidates are more tractable for a small molecule or antibody to actually hit — a cell-surface receptor is a much easier drug target than an intracellular scaffolding protein, independent of how essential or tumor-selective it is.

## Technical concepts & decisions

### Local environment and repository (2026-09-13)

Set up a dedicated conda environment (`target-discovery`, Python 3.10) with pandas, numpy, scipy, matplotlib, seaborn, `lifelines` (for the Week 4 survival analysis), and jupyter/ipykernel, and registered it as a Jupyter kernel. Initialized a git repository with `data/raw/{depmap,tcga,gtex,hpa}/` kept separate from `data/processed/` — raw downloads should stay untouched so any cleaning, filtering, or mapping decision can always be re-checked against the original file rather than against something already modified.

One quirk worth remembering: `conda activate` in this shell doesn't reliably put the env's `python3` first on `PATH` (Homebrew's system Python wins instead). Calling the interpreter by its full path — `/Applications/miniconda3/envs/target-discovery/bin/python3` — avoids silently running analysis code against the wrong Python with none of the project's packages installed.

### DepMap's public data requires no account

I initially assumed downloading DepMap's files would need a registered account, based on an automated request hitting a Cloudflare bot-verification page. That assumption was wrong: DepMap's public data (Chronos CRISPR scores, cell line metadata) is fully open access — the bot-check is just anti-scraping protection that any normal browser passes automatically, and there's no sign-up flow to look for. As of the 25Q2 release, DepMap also stopped bulk-publishing full releases to Figshare, so files now come from the portal's own "All Data"/"Custom Downloads" tabs directly rather than a single archive link.

### DepMap release: 26Q1

Downloaded files: `CRISPR Gene Effect.csv` (1,208 cell lines × ~18,531 genes of Chronos gene-effect scores) and `Model Data.csv` (2,154 cell line/model records × 49 metadata columns), both from the **DepMap Public 26Q1** release. Recording the exact release matters because DepMap's cell-line panel, gene list, and even the Chronos scores themselves shift slightly between quarterly releases — any candidate gene ranking this project produces is only reproducible if it's tied to a specific release, not "DepMap" in general.

### Defining the TNBC cell-line set: `ModelSubtypeFeatures`, not a manual mapping

This was the biggest open item carried from Week 0: how to decide which DepMap breast cancer cell lines actually count as TNBC, without building a manual ER/PR/HER2 receptor-status lookup from some external, possibly-inconsistent source.

It turns out `Model Data.csv` already carries this directly. Filtering to `OncotreeLineage == "Breast"` gives 96 cell lines. Most of those also have a `ModelSubtypeFeatures` column — a short free-text molecular-subtype description, with values like `basal_A TNBC`, `basal_B TNBC`, `luminal TNBC`, `basal TNBC`, and plain `TNBC`, alongside non-TNBC labels such as `ER+`, `HER2+`, and `luminal ER+, PR+`. Filtering for any value containing the substring `"TNBC"` gives **34 TNBC-labeled breast cell lines**, of which **25 have CRISPR screen data** in `CRISPR Gene Effect.csv` — a workable-sized comparison group for Week 2's dependency analysis.

A few caveats to carry into Week 1/2 rather than gloss over:
- **15 of the 96 breast lines have no `ModelSubtypeFeatures` value at all** (missing, not "confirmed not TNBC"). These should stay excluded from *both* the TNBC group and the "confirmed non-TNBC" comparison group, rather than being silently counted as non-TNBC just because they lack the label.
- **The `basal_A`/`basal_B`/`luminal` prefixes** on some TNBC entries reflect a finer intrinsic-subtype scheme layered on top of receptor-status TNBC. For now the plan is to treat every `*TNBC` label as one group, since the project's question is about TNBC as a whole — but if a later finding looks like it's really only true of one basal/luminal-TNBC subgroup, that's worth calling out explicitly rather than reporting it as a TNBC-wide result.
- This resolves the DepMap half of the cell-line-mapping open decision. The equivalent decision for TCGA-BRCA (which subtype field to use, and the exact inclusion rule) is still open, and will need the same "check the real column before assuming" approach once the clinical file is downloaded.

## Week 0: Setup and scope

- [x] Set up the Python environment and Jupyter kernel.
- [x] Create the project repository.
- [x] Choose TNBC as the cancer focus.
- [x] Record the TNBC rationale.
- [x] Download the current Chronos gene-effect and cell-line metadata files.
- [x] Inspect the DepMap files and record their release/version.

**Week 0 outcome:** The biological question is defined: which genes are selectively important in TNBC and plausible as therapeutic targets? Environment, repository, and DepMap files (26Q1) are in place.

## Week 1: Collect data and understand it

- [ ] Load and lightly clean the DepMap gene-effect matrix.
- [x] Define the TNBC cell-line set using subtype annotations or a documented mapping.
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
