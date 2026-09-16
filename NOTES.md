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

### What Mann-Whitney U actually does, in plain terms

Take a gene's dependency scores from both groups (25 TNBC lines, ~1,181 others), dump all of them into one pile, and rank every value from most negative to most positive — forgetting for a moment which group each one came from. If TNBC and the other lines are really no different for this gene, TNBC's ranks should land randomly scattered through that pile. If TNBC's values are genuinely more essential (more negative), TNBC's ranks should cluster down toward the "most negative" end more than random scattering would produce. Mann-Whitney U measures exactly how lopsided that clustering is, and turns it into a p-value — the test never looks at the actual numbers, only their order. That's what makes it hard for one weird cell line to distort the result: an outlier can only occupy one rank slot, whereas it could drag a group's *average* around by a lot.

### p-value vs. q-value, in plain terms

A **p-value** answers a question about one gene in isolation: "if there's truly no real difference here, how likely is it I'd see a result this extreme just by chance?" A tiny p-value for one gene sounds very convincing on its own.

The catch: this project doesn't test one gene, it tests ~18,000 of them at once. Run 18,000 independent chance-based tests and, even if nothing real is happening anywhere, roughly 900 of them will still look "significant" at p<0.05 purely by luck — the same way a coin will eventually land on 8 heads in a row if you flip it enough times. A **q-value** corrects for this: it asks "of all the genes I'd call significant at this cutoff, what fraction do I expect to actually be false alarms, given how many tests I ran?" A q-value is always equal to or larger than its p-value — the correction can only make a result look less impressive, never more. **Any real decision in this project (what makes the shortlist) is based on q-values, not raw p-values** — the p-value alone would badly overstate how many "significant" genes there really are.

### Choosing the essentiality test: Welch's t-test vs. Mann-Whitney U, run side by side

Talked through before implementing rather than picking one upfront. The core tension: the TNBC group is only 25 cell lines against ~1,181 others, and a t-test's validity leans on the *mean* being a stable summary of each gene's TNBC-group scores — one unusual cell line among only 25 has real leverage to swing a mean-based test. Mann-Whitney U (rank-based) doesn't have that problem, at some cost in statistical power if the data really is well-behaved. Rather than guess which mattered more here, ran **both**, for every gene, and compared them empirically — same instinct as the ADMET project's RF-vs-XGBoost comparisons.

**Comparison group definition:** "TNBC" is the 25 CRISPR-screened lines from Week 1's mapping; "other" is *every remaining* DepMap line with CRISPR data, **except** the 2 breast lines with no `ModelSubtypeFeatures` value at all — same "unknown isn't automatically the other bucket" rule used for the TNBC mapping itself, applied here so those 2 unlabeled lines can't quietly dilute the comparison group with a possible unlabeled TNBC line.

**Result — the two tests broadly agree, but the disagreement at the threshold matters:** across all ~17,900 testable genes, the two tests' p-values correlate strongly (Spearman ρ = 0.87), so in the big picture they're measuring the same signal. But at a practical significance threshold (q < 0.10, restricted to genes more essential in TNBC), the t-test calls **8 genes** significant and Mann-Whitney calls **13** — only **6 genes overlap (40% of the union)**. High overall correlation and low overlap-at-threshold aren't a contradiction: it means the two tests agree on the broad ranking but disagree at the margin, exactly where a "shortlist" decision actually gets made. Given the group-size imbalance reasoning above, **Mann-Whitney's ranking is the one used for the actual shortlist** (`u_q` column, sorted ascending), with the t-test's `t_q` kept alongside every row for comparison rather than discarded.

Also notable: relatively few genes clear even a relaxed q < 0.10 threshold (8-13, not 30-50) — a real signal that TNBC-selective essentiality, at genome-wide multiple-testing correction, is a comparatively weak/subtle effect with only 25 cell lines' worth of power, not a sign anything is broken. The plan's 30-50-gene shortlist is produced by taking the top-N by rank instead of a hard significance cutoff (see `notebooks/02_selective_essentiality.ipynb`), which is a materially different (softer) standard than "statistically significant genome-wide" — worth remembering when deciding how much weight any individual candidate can bear later.

Full results (all ~17,900 genes, both tests' p/q-values, effect size) saved to `data/processed/depmap_tnbc_essentiality.csv`; the top-40 shortlist to `data/processed/depmap_tnbc_shortlist.csv`.

### The biological plausibility check found a real problem — and fixed it

The raw statistical shortlist looked reasonable at a glance, but checking it against biology (this project's own guardrail: don't present a ranking as a finding until it's checked) surfaced two concrete, fixable problems, using data already downloaded for this project — no new source needed:

1. **Pan-essential genes contaminating the "TNBC-selective" list.** Several of the top genes by q-value — `SNRPF`, `LSM2`, `POLR3A`, `SMU1`, `CCT3`, `PSMA5` — are core spliceosome/proteasome/RNA-Pol-III machinery, essential in *every* cell line (pan-cancer mean Chronos score between -2.0 and -3.2; Chronos is calibrated so -1 ≈ the median of known common-essential genes). With only 25 TNBC lines, even a universally essential gene's small-sample mean can drift slightly more negative than the huge comparison group's mean by chance, which survives multiple-testing correction without meaning anything TNBC-specific. This is a well-known pitfall in differential-essentiality analysis that the first pass didn't filter for. **Fix:** exclude any gene with a pan-cancer mean effect below -1.0 before ranking.
2. **A likely sex-chromosome artifact.** The TNBC group is 100% female (25/25); the "other" comparison group is majority male (658 male vs. 462 female). `AMELY` (a Y-linked tooth-enamel gene) made the original shortlist despite having **zero expression in real TNBC tumors** — its "TNBC-selective" signal is far more plausibly a sex-linked technical artifact than real biology, and a purely statistical ranking has no way to see that on its own. **Fix:** require real expression in TCGA-BRCA TNBC tumors (median log2(RSEM+1) > 1) — this also caught several other implausible hits (an olfactory receptor `OR4K2`, a salivary gland protein `PRB4`, a neuronal ion channel `TRPC5`, none of which are expressed in breast tissue at all).

(One technical fix needed along the way: matching DepMap genes to TCGA's 2016-vintage expression file by gene *symbol* silently failed for ~180 genes whose official symbol has since changed — switched to matching by **Entrez ID**, parsed from DepMap's own raw column headers, which matched 17,755 of 17,931 genes instead.)

**After both filters, the revised shortlist (`data/processed/depmap_tnbc_shortlist_v2.csv`) is materially cleaner** — no more pan-essential machinery genes or unexpressed genes at the top. Checked five of the new top candidates against actual literature (not memory, to avoid asserting an unverified biological claim):

| Gene | Literature match |
|---|---|
| **LY6E** | **Strong, TNBC-specific** — independently published (2025) as a TNBC "theranostic target": high membrane expression specifically in TNBC cell lines, low in normal breast epithelium, confirmed in a xenograft model, significantly elevated in TNBC tissue (p<0.0001). |
| **CDKN1A (p21)** | Moderate, TNBC-specific — documented role in TNFα-induced, MMP9-dependent invasion in TNBC cell lines, and in breast-cancer-stem-cell survival after oxidative stress. |
| **ZFX** | Moderate, breast-cancer-general (not TNBC-specific in what was found) — knockdown suppresses breast cancer proliferation via Akt/ERK2; oncogenic role also reported in several other cancers. |
| **BIRC7 (Livin)** | Moderate, breast-cancer-general — elevated expression correlates with malignancy grade; linked to chemoresistance and trastuzumab resistance. |
| **KIF2C** | Unconfirmed — no direct match found in this search; would need a more targeted lookup before drawing any conclusion either way. |

**`LY6E` landing near the top of a DepMap dependency ranking, then turning out to already be independently published as TNBC-selective by a completely different method (RNA-seq + protein + xenograft), is the real "recovers known biology" result for Week 2** — not a guarantee every candidate is real, but genuine, independent corroboration for at least one. `KIF2C` is a reminder that clearing every filter still isn't the same as being validated; some candidates just need a closer look later.

**The number to carry into Week 3 is `depmap_tnbc_shortlist_v2.csv`, not the original `depmap_tnbc_shortlist.csv`.**

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

- [x] Compare gene dependency in TNBC cells with other cell lines.
- [x] Use an appropriate statistical test and correct for multiple comparisons.
- [x] Rank genes by dependency effect and statistical evidence.
- [x] Create a shortlist of approximately 30–50 candidates.
- [x] Check whether the analysis recovers known TNBC biology.

**Week 2 outcome — complete.** A plausibility-filtered ranked list of genes TNBC cells appear to depend on preferentially (`data/processed/depmap_tnbc_shortlist_v2.csv`), with the raw statistical ranking, the two biological problems found and fixed (pan-essential contamination, a likely sex-chromosome artifact), and a literature check of the survivors all in `notebooks/02_selective_essentiality.ipynb` and the "biological plausibility check" section above.

## Week 3: Check tumor selectivity and safety

- [x] Compare candidate expression in TNBC tumors with normal tissue baselines.
- [x] Prioritize genes that are both selectively essential and tumor-enriched.
- [x] Flag expression in critical normal tissues as a potential safety concern.
- [ ] Optionally add Human Protein Atlas protein-class and druggability annotations. (skipped for now — optional)

**Week 3 outcome — complete.** `notebooks/03_tumor_selectivity_safety.ipynb` adds tumor-vs-normal fold change and a critical-tissue safety flag to every Week 2 candidate, producing `data/processed/depmap_tnbc_week3_final.csv`.

### Resolving the TCGA-normal-vs-GTEx open decision: it wasn't really either/or

This had sat as an open decision since Week 0. Turned out the two datasets answer genuinely different questions, so both get used rather than picking one:
- **Tumor selectivity** (is the gene overexpressed in the tumor?) uses TCGA-BRCA's own **112 matched-normal breast samples** — same study, same sequencing pipeline, so the comparison isn't confounded by cross-study batch effects.
- **Safety** (is the gene critical in vital organs?) needs GTEx, since TCGA-BRCA only has breast tissue — it can't answer "is this gene important in the heart" at all.

### KIF2C: the standout candidate, with three independent lines of evidence

- **DepMap:** selectively essential in TNBC (Week 2).
- **TCGA-BRCA:** massively tumor-overexpressed — log2 fold change **+3.35** (roughly 10x) over matched normal breast, q < 1e-58.
- **GTEx safety:** low expression in critical tissues (max 1.8 TPM across heart/liver/whole blood) — a favorable safety profile.
- **Literature:** independently and extensively published as overexpressed in breast cancer (including ER-negative disease) and correlated with poor prognosis across multiple TCGA cohort studies, proposed as a prognostic biomarker in its own right.

Three independent lines of evidence (essentiality, tumor overexpression, published literature) converging on one gene is a much stronger result than any single signal alone — exactly what Week 4's composite score is meant to formalize. Worth remembering: Week 2's literature search had called KIF2C "unconfirmed" — that search was specifically about a CRISPR-essentiality angle, which genuinely has no direct published hit. The overexpression/prognosis angle checked here is a different question, and a much better-supported one. A "no hit" on one search angle doesn't mean "no biology" — it's worth trying a different angle before writing a candidate off.

### Real safety concerns, flagged rather than hidden

- **`IFI6`** (log2fc +2.32) and **`LY6E`** (Week 2's strongest literature-validated hit) both show high critical-tissue expression (71.7 and 175.5 TPM) — both are interferon-stimulated genes broadly expressed in circulating immune cells, plausibly explaining a Whole Blood signal specifically. Doesn't rule either out, but it's a real caution to carry forward.
- **`H2AC6`** (a core histone gene) has the highest critical-tissue value in the whole list (256 TPM) alongside strong tumor overexpression — histones are highly expressed in any proliferating tissue (including bone marrow), so this reads as a general-proliferation signal, not TNBC-specific biology.
- **`SIGLEC8`**, on inspection, is a known eosinophil/mast-cell surface marker — its apparent "tumor overexpression" more plausibly reflects immune cells infiltrating the bulk tumor sample than the cancer cells themselves. A general caution: bulk RNA-seq can't distinguish tumor-cell signal from infiltrating-immune-cell signal, worth remembering for any candidate going forward.

**Safety flag thresholds used** (a documented judgment call, not a universal standard): GTEx critical-tissue (heart/liver/whole blood, the latter as the standard bone-marrow proxy) max TPM < 5 = low, 5–20 = moderate, > 20 = high. Of the 40 candidates: 12 low, 12 moderate, 16 high.

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
