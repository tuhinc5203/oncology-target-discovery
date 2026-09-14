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

**Why it matters:** DepMap runs genome-wide CRISPR knockout screens across hundreds of cancer cell lines and reports a "gene effect" score (via the Chronos algorithm) for every gene in every cell line — essentially, how much that cell line's growth/viability drops when the gene is knocked out. More negative means more essential to that cell line's survival. This is the "does the cancer actually depend on this gene" signal, and it's the genome-wide, in-silico analog of exactly what target validation does at the bench one gene at a time.

**Why this source, specifically:** DepMap is essentially the only dataset of its kind — no other public resource runs CRISPR dependency screens across this many cancer cell lines with this much cell-line-level metadata (subtype annotations, lineage, etc.). The real choice here wasn't *which* dependency dataset, it was *which release*: went with **26Q1**, the current quarterly release at the time of download, rather than an older cached version, so the cell-line panel and Chronos scores match what anyone re-checking the portal today would see.

### TCGA-BRCA (tumor expression + clinical outcomes)

**Why it matters:** The Cancer Genome Atlas's breast cancer cohort provides RNA-seq expression and clinical/survival data from real patient tumors. This answers two different questions from DepMap: is a gene that looks essential in TNBC cell lines actually turned up in real TNBC tumors (not just a cell-culture artifact)? And do patients whose tumors express it highly have worse outcomes? Together these move a candidate from "cell-line finding" toward "clinically plausible."

**Why this source, specifically:** TCGA-BRCA itself was the obvious dataset (it's the standard, large, public breast-cancer cohort with matched expression + clinical + survival data), but there are several different ways to actually pull it, and that choice mattered:
- **UCSC Xena** (the project plan's original suggestion, "simplest way to get pre-processed TCGA data") turned out to be blocked from this environment by the same kind of automated bot-check DepMap has — even though the intended workflow is a no-login browser download, it couldn't be scripted here.
- **Raw GDC** (the Genomic Data Commons' own per-sample files) would have meant assembling ~1,100 individual sample files into one matrix — correct, but a lot of extra plumbing for what's ultimately the same underlying data.
- **cBioPortal's REST API** works fine from here, but pulling a whole-genome expression matrix through it means paginating gene-by-gene in batches — thousands of small requests for one matrix.
- **Broad Institute's GDAC Firehose archive** (the `stddata__2016_01_28` BRCA run) won out: it's a plain public HTTP host with no bot-check, serving the expression matrix as one already-merged flat file — the same underlying data cBioPortal's own `brca_tcga` study is built from, just fetched directly instead of through a paginated API. That made it fully scriptable (`scripts/download_tcga.py`).
- For the *clinical* side specifically, chose the archive's full CDE table over cBioPortal's newer PanCancer Atlas study, because that newer study only carries a coarse PAM50-style `SUBTYPE` label — TNBC's real clinical definition needs actual ER/PR/HER2 IHC/FISH receptor status, which only the older archive's CDE table has (see "Defining TCGA-BRCA's TNBC patient set" below).

### GTEx (normal tissue baseline)

**Why it matters:** The Genotype-Tissue Expression project profiles gene expression across dozens of normal (non-cancerous) human tissues. This is the safety/therapeutic-window check: a gene can be essential *and* tumor-overexpressed and still be a bad target if it's also highly expressed in the heart, liver, or bone marrow — a drug hitting it would likely cause dose-limiting toxicity before it could work on the tumor. This is the same kind of judgment a target-validation scientist applies before recommending a target for further investment.

**Why this source, specifically:** like DepMap, GTEx has essentially one canonical source (the GTEx project's own public data), so the choice was about *version*, not provider. The first file found was **v8** (2017, the release most tutorials/papers still cite), but a newer **v11** release exists (August 2025, updated GENCODE 47 gene annotation over v10, same underlying samples) — switched to that for current gene annotation and finer tissue resolution (68 tissues vs. v8's 54, from more granular tissue-site splitting).

### Human Protein Atlas (optional — druggability context)

**Why it matters:** Protein-class annotations (kinase, cell-surface receptor, secreted protein, etc.), planned as an optional Week 3 addition. Used to flag which surviving candidates are more tractable for a small molecule or antibody to actually hit — a cell-surface receptor is a much easier drug target than an intracellular scaffolding protein, independent of how essential or tumor-selective it is.

**Why this source:** HPA is the standard public reference for protein-class/tissue-expression annotation at this level of curation; not yet downloaded since it's an optional Week 3 addition, not a Week 0/1 requirement.

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
- This resolves the DepMap half of the cell-line-mapping open decision. The equivalent decision for TCGA-BRCA (which subtype field to use, and the exact inclusion rule) is resolved below.

### Reproducible downloads: TCGA and GTEx, unlike DepMap, can be scripted

DepMap's download needed a real browser (see above). TCGA-BRCA and GTEx turned out not to: both are served from plain public hosts with no bot-check, so their downloads are captured as real scripts — `scripts/download_tcga.py` and `scripts/download_gtex.py` — rather than one-off manual steps. Verified reproducible directly: re-ran `download_tcga.py` into a scratch directory and diffed the result against the files already in `data/raw/tcga/` — byte-identical.

- **GTEx v11** comes straight from its public Google Cloud Storage bucket (`storage.googleapis.com/adult-gtex/...`), no auth of any kind.
- **TCGA-BRCA** comes from the Broad Institute's GDAC Firehose archive (`stddata__2016_01_28` run for BRCA) — the same underlying data cBioPortal's `brca_tcga` ("TCGA, Firehose Legacy") study is built from, just fetched as flat files instead of through cBioPortal's paginated REST API (which would have needed thousands of small requests to pull a whole-genome expression matrix).

### GTEx release: v11

Downloaded `GTEx_Analysis_v11_gene_median_tpm.gct.gz` — median TPM per gene per tissue, **74,628 genes × 68 tissues**. This is GTEx's current release (August 2025 GENCODE 47 annotation update over v10; no new samples/donors versus v10). Recording the exact version matters for the same reason as DepMap's release: GTEx's gene annotation and tissue groupings have changed across versions (v8's 54 tissues vs. v11's 68, from finer tissue-site splitting), so a safety-flag result should be tied to "v11", not "GTEx" in general.

### Defining TCGA-BRCA's TNBC patient set: real IHC/FISH receptor status, not just a molecular-subtype label

TNBC is clinically defined by receptor status — ER-negative, PR-negative, and HER2-negative — not by a PAM50-style molecular subtype label. The widely-used cBioPortal PanCancer Atlas BRCA study (`brca_tcga_pan_can_atlas_2018`) only carries a coarse `SUBTYPE` field (PAM50-derived, e.g. "Basal-like"), which is a common proxy for TNBC in the literature but isn't the actual clinical definition. The Broad Firehose archive's full clinical CDE table (`All_CDEs.txt`, same underlying source as cBioPortal's older `brca_tcga` study) carries the real pathology fields instead:

- `breast_carcinoma_estrogen_receptor_status`
- `breast_carcinoma_progesterone_receptor_status`
- `lab_proc_her2_neu_immunohistochemistry_receptor_status` (HER2 IHC score)
- `lab_procedure_her2_neu_in_situ_hybrid_outcome_type` (HER2 FISH/ISH result)

HER2 needs its IHC and FISH results combined, not read from either field alone, because of how HER2 testing actually works clinically: IHC 0/1+ is called negative outright, IHC 3+ is called positive outright, but IHC 2+ ("equivocal") requires a reflex FISH test to resolve — a molecule with IHC-equivocal doesn't have a real answer until FISH is checked. `get_tnbc_patient_barcodes()` in `data_utils.py` implements exactly this: HER2 is treated negative if IHC says negative outright, *or* IHC is equivocal and FISH says negative; TNBC requires ER negative, PR negative, and that combined HER2-negative call. Patients with a missing or indeterminate result on any of the three markers are excluded from the TNBC group rather than defaulted to non-TNBC — same "unknown isn't automatically the other bucket" principle applied to DepMap's missing `ModelSubtypeFeatures` values above.

Result on the real data: **143 of 1,097 patients (13%) are TNBC** — squarely inside TNBC's well-documented ~10–20% share of breast cancers, a reassuring sanity check that the rule is behaving as expected before it's used for anything downstream. **142 of those 143 have a matching primary-tumor expression sample** in the RNA-seq matrix (one patient's clinical record has no paired expression data), giving a solid-sized cohort for Week 3's tumor-selectivity comparison.

### TCGA-BRCA data downloaded

- **Expression:** `BRCA.rnaseqv2_RSEM_genes_normalized.data.txt` — RSEM-normalized RNA-seq V2 counts, **20,531 genes × 1,212 samples** (1,093 of which are primary tumor samples, identified by the `-01` sample-type code in the TCGA barcode; the rest are normals/other sample types — relevant to the still-open "matched normal vs. GTEx baseline" decision).
- **Clinical:** `All_CDEs.txt` (full clinical CDE table, used for receptor status above) and `BRCA.clin.merged.picked.txt` (Broad's curated one-value-per-field picks, which carry `vital_status`/`days_to_death`/`days_to_last_followup` for Week 4's survival analysis) — **1,097 patients**.
- Sample barcodes in the expression file (`TCGA-3C-AAAU-01A-11R-A41B-07`, uppercase, full-length) don't match clinical file columns (`tcga-3c-aaau`, lowercase, patient-level) directly — `tcga_patient_barcode()` in `data_utils.py` handles the conversion.

## Week 0: Setup and scope

- [x] Set up the Python environment and Jupyter kernel.
- [x] Create the project repository.
- [x] Choose TNBC as the cancer focus.
- [x] Record the TNBC rationale.
- [x] Download the current Chronos gene-effect and cell-line metadata files.
- [x] Inspect the DepMap files and record their release/version.

**Week 0 outcome:** The biological question is defined: which genes are selectively important in TNBC and plausible as therapeutic targets? Environment, repository, and DepMap files (26Q1) are in place.

## Week 1: Collect data and understand it

- [x] Load and lightly clean the DepMap gene-effect matrix.
- [x] Define the TNBC cell-line set using subtype annotations or a documented mapping.
- [x] Download TCGA-BRCA expression and clinical data.
- [x] Use molecular subtype annotations rather than treating every breast tumor as TNBC.
- [x] Download GTEx median expression by tissue.
- [x] Record dimensions, missingness, and distributions.
- [x] Write a short explanation of what each dataset contributes.

**Week 1 outcome:** Clean, understood datasets and a defensible definition of the TNBC analysis groups. Full EDA (dimensions, missingness, distributions, with plots) in `notebooks/01_data_eda.ipynb`.

### EDA findings worth remembering (`notebooks/01_data_eda.ipynb`)

- **DepMap:** 3.96% of the gene-effect matrix is missing, concentrated in ~8% of genes (every cell line has *some* missing genes, but most genes are complete across the whole panel) — consistent with inconsistent screening/QC across the panel, not a systemic problem. Score distribution is unimodal, centered just below 0, with a long negative (essential-gene) tail — the expected shape for a genome-wide CRISPR screen.
- **TCGA expression:** zero missing values (RSEM normalization produces a dense matrix by construction), but heavily right-skewed like any RNA-seq count data — `log2(x + 1)` is the planned transform for Week 2/3 comparisons, same reasoning as the ADMET project's logS transform. The single most extreme raw value belongs to **SCGB2A2 (mammaglobin-B)** — a well-known, extremely breast-tissue-specific marker, so an extreme value for it is real biology, not a parsing bug. The highest-median-expression genes (`COL1A1`, `ACTB`, `EEF1A1`, `FN1`, ...) are exactly the housekeeping/collagen genes expected to dominate bulk tissue RNA-seq — a useful sanity check that the matrix is behaving like real expression data. 1,093 of 1,212 samples are primary tumor (`-01` code); the rest are matched-normal/other types, feeding the still-open normal-baseline decision.
- **TCGA clinical:** HER2 FISH is missing for 62% of patients, which looks alarming in isolation but isn't a data problem — per the ASCO/CAP reflex rule, FISH is only ordered when IHC comes back equivocal (2+), so most patients' HER2 status is already resolved by IHC alone and simply never needed a FISH test. Similarly, `days_to_death` (86% missing) and `days_to_last_followup` (14% missing) are two sides of one coin — a patient has one or the other depending on `vital_status` (0% missing), never both. Both are the expected shape of survival data, not gaps to fix, and exactly what Week 4's Kaplan-Meier/Cox analysis is built to consume.
- **GTEx:** zero missing values, but 54% of gene/tissue combinations are exactly 0 — expected for tissue-specific expression, where most genes simply aren't expressed in most tissues. Same right-skew/log2 pattern as TCGA.

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
