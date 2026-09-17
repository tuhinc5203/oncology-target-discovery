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
- [x] Optionally add Human Protein Atlas protein-class and druggability annotations.

**Week 3 outcome — complete.** `notebooks/03_tumor_selectivity_safety.ipynb` adds tumor-vs-normal fold change, a critical-tissue safety flag, and HPA druggability annotations to every Week 2 candidate, producing `data/processed/depmap_tnbc_week3_final.csv`.

**A note on the HPA step itself:** this was originally marked "skipped for now — optional" without actually asking about it — I made that call unilaterally based on the plan's own "optional" wording, rather than flagging it as a real decision. Worth remembering: an "optional" label in a plan is a reason to check in, not a reason to silently decide for someone. Went back and did it once this was pointed out.

### Resolving the TCGA-normal-vs-GTEx open decision: it wasn't really either/or

This had sat as an open decision since Week 0. Turned out the two datasets answer genuinely different questions, so both get used rather than picking one:
- **Tumor selectivity** (is the gene overexpressed in the tumor?) uses TCGA-BRCA's own **112 matched-normal breast samples** — same study, same sequencing pipeline, so the comparison isn't confounded by cross-study batch effects.
- **Safety** (is the gene critical in vital organs?) needs GTEx, since TCGA-BRCA only has breast tissue — it can't answer "is this gene important in the heart" at all.

### KIF2C: the standout candidate, with four independent lines of evidence

- **DepMap:** selectively essential in TNBC (Week 2).
- **TCGA-BRCA:** massively tumor-overexpressed — log2 fold change **+3.35** (roughly 10x) over matched normal breast, q < 1e-58.
- **GTEx safety:** low expression in critical tissues (max 1.8 TPM across heart/liver/whole blood) — a favorable safety profile.
- **Literature:** independently and extensively published as overexpressed in breast cancer (including ER-negative disease) and correlated with poor prognosis across multiple TCGA cohort studies, proposed as a prognostic biomarker in its own right.
- **HPA (with an honest caveat, see below):** a real, if statistically conservative, survival signal in HPA's own analysis too.

Four independent lines of evidence (essentiality, tumor overexpression, published literature, HPA's own survival analysis) converging on one gene is a much stronger result than any single signal alone — exactly what Week 4's composite score is meant to formalize. Worth remembering: Week 2's literature search had called KIF2C "unconfirmed" — that search was specifically about a CRISPR-essentiality angle, which genuinely has no direct published hit. The overexpression/prognosis angle checked here is a different question, and a much better-supported one. A "no hit" on one search angle doesn't mean "no biology" — it's worth trying a different angle before writing a candidate off.

### HPA: druggability, and a genuinely interesting statistical discrepancy

Added after initially, and wrongly, being skipped as "optional." Downloaded `proteinatlas.tsv` (Human Protein Atlas release **25.1**, Ensembl 109) — one row per gene (20,162 genes), with columns for protein class, subcellular location, and (very usefully) HPA's own precomputed survival-prognostic call for each gene in each cancer type, based on their own Kaplan-Meier analysis of TCGA data.

**Checking `KIF2C` against HPA's breast-cancer prognostic call turned up something that looked like a contradiction at first:** HPA labels it **"unprognostic"** (p=0.0714 in TCGA, p=0.0164 in HPA's own separate validation cohort) — which seems to conflict with the extensive published literature (checked in Week 3 above) linking `KIF2C` to poor breast cancer survival. Investigated rather than picked around: **HPA deliberately uses a strict p < 0.001 cutoff** to call something "prognostic" (confirmed via their own published methodology), specifically because they're testing genome-wide and want to guard against false positives — the same underlying motivation as this project's own FDR correction, just implemented as one fixed strict bar instead of an adjusted one. A p=0.0164 is a real, meaningful result; it simply doesn't clear that particular conservative bar in a *single* cohort's analysis, whereas the published meta-analyses pooled many independent cohorts together, giving far more statistical power. **Both results are correct at the same time** — this is exactly why checking a claim from two different angles (an FDR-based test here, a fixed-threshold test there) is worth doing, rather than trusting either one blindly. Every other checked candidate (`LY6E`, `CDKN1A`, `ZFX`, `BIRC7`, `IFI6`, `H2AC6`) also came back "unprognostic" by this same strict standard — a good general caution that HPA's label is a high bar, not proof of "no association."

**Druggability read on the candidates:** `KIF2C`, `CDKN1A`, `ZFX`, `H2AC6`, and `BIRC7` are all classified `Predicted intracellular proteins` — mostly nuclear, nothing on the cell surface, which rules out an antibody-drug approach and means a small molecule would be needed instead (harder, though not unprecedented — kinesin motor proteins like `KIF2C` are an established drug-target class, with published inhibitors for a related kinesin, KIF11/Eg5, reaching clinical trials). `LY6E` came back `Predicted membrane proteins` — genuinely more tractable, and consistent with the earlier literature describing it as expressed "on the membrane" of TNBC cells specifically. None of this changes any candidate's essentiality/selectivity/safety status — it's an added, separate dimension: `KIF2C` remains the strongest *biological* candidate, but `LY6E` may be the more practically druggable one.

### Real safety concerns, flagged rather than hidden

- **`IFI6`** (log2fc +2.32) and **`LY6E`** (Week 2's strongest literature-validated hit) both show high critical-tissue expression (71.7 and 175.5 TPM) — both are interferon-stimulated genes broadly expressed in circulating immune cells, plausibly explaining a Whole Blood signal specifically. Doesn't rule either out, but it's a real caution to carry forward.
- **`H2AC6`** (a core histone gene) has the highest critical-tissue value in the whole list (256 TPM) alongside strong tumor overexpression — histones are highly expressed in any proliferating tissue (including bone marrow), so this reads as a general-proliferation signal, not TNBC-specific biology.
- **`SIGLEC8`**, on inspection, is a known eosinophil/mast-cell surface marker — its apparent "tumor overexpression" more plausibly reflects immune cells infiltrating the bulk tumor sample than the cancer cells themselves. A general caution: bulk RNA-seq can't distinguish tumor-cell signal from infiltrating-immune-cell signal, worth remembering for any candidate going forward.

**Safety flag thresholds used** (a documented judgment call, not a universal standard): GTEx critical-tissue (heart/liver/whole blood, the latter as the standard bone-marrow proxy) max TPM < 5 = low, 5–20 = moderate, > 20 = high. Of the 40 candidates: 12 low, 12 moderate, 16 high.

## Week 4: Test clinical relevance and score candidates

- [x] Run Kaplan-Meier analysis for the leading candidates.
- [x] Run Cox models for the strongest candidates.
- [x] Define and explain the composite score.
- [x] Combine dependency, tumor selectivity, and survival signals; keep safety and druggability as annotations rather than blending them in.
- [x] Produce a final ranked list of the 15 candidates.

**Week 4 progress:** Complete. Survival analysis and composite scoring are both done (`notebooks/04_survival_analysis.ipynb`), producing `data/processed/depmap_tnbc_final_ranked_targets.csv`.

### Narrowing to 15 before survival analysis: not either/or with the full 40

Rather than run survival analysis on all 40 Week 3 candidates, first filtered to the 20 that are actually tumor-enriched (`log2fc_tumor_vs_normal > 0`) — genes that don't meet that bar don't fit the project's own definition of a good candidate regardless of what a survival test might show — then ranked by combined essentiality + tumor-selectivity strength and took the top 15. Two real benefits: survival testing needs its own multiple-testing correction, and correcting across 15 tests preserves meaningfully more power than correcting across 40; and it's a more defensible narrative ("applied established criteria before spending analysis on survival" beats "tested everything and hoped something stuck"). The accepted tradeoff: a gene that's essential, safe, and genuinely prognostic but not measurably tumor-overexpressed in bulk RNA-seq wouldn't get tested here — a real but deliberate risk, not an oversight.

### A real reproducibility bug caught and fixed: notebooks were silently running under the wrong Python environment

While setting up Week 4's notebook (the first to need `lifelines`), execution failed with `ModuleNotFoundError: No module named 'lifelines'` — even though `lifelines` is installed in the `target-discovery` conda environment. Investigated the actual mechanism rather than just patching around it with a flag:

1. Every notebook so far had been built programmatically (via `nbformat`, not a real Jupyter session), so none of them ever had `kernelspec` metadata saved in the file. With no kernelspec to go on, `nbconvert` falls back to looking for a kernel literally named `"python3"`.
2. It turns out **every** conda environment that has `ipykernel` installed automatically gets its own `"python3"` kernel registered (a side effect of installing `ipykernel`, separate from the `target-discovery` kernel that was deliberately registered by name early in this project). The auto-generated one's launch command is just the bare word `"python"` — not a full path.
3. A bare `"python"` command gets resolved by the operating system using the **calling shell's `PATH`** at the moment the kernel subprocess actually starts — not by which Python happened to launch the `nbconvert` command itself, and not by which directory the kernelspec file lives in. This shell's `PATH` has base conda's `bin` directory ahead of anywhere `target-discovery`'s would be (because `conda activate target-discovery` doesn't work reliably in this shell — the same PATH issue already noted in `CLAUDE.md`'s "Local dev gotcha," now shown to affect more than just manually-run commands). So `"python"` resolved to **base conda's Python 3.11**, every time, regardless of which Python launched `nbconvert`.
4. The one kernel that *did* work correctly the whole time is the deliberately-registered `target-discovery` kernel, because its kernelspec uses a full, unambiguous path (`/Applications/miniconda3/envs/target-discovery/bin/python`) instead of a bare command — it was never exposed to this `PATH` ambiguity.

**This meant Weeks 1–3's notebooks had actually been executing under the base environment this whole time, not the pinned `target-discovery` environment as documented.** Checked directly rather than assumed: re-ran all three notebooks with the kernel explicitly forced to `target-discovery`, and diffed every output against what was already committed. **All outputs were identical** (aside from one harmless one-time "building font cache" message that only prints the first time matplotlib runs in a fresh environment, and floating-point differences at roughly the 15th decimal digit in the saved CSVs — see below for why that's expected and harmless here). Real reassurance, but it could have gone differently, and shouldn't be relied on by luck going forward.

**Fixed at the actual root cause, not patched around:** every notebook now has explicit `kernelspec` metadata (pointing at the `target-discovery` kernel specifically, the one with the unambiguous full path) saved directly in the `.ipynb` file. This was verified to be sufficient **on its own** — re-ran a disposable copy of `notebooks/04_survival_analysis.ipynb` with `jupyter nbconvert --execute` and **no kernel-related flag at all**, and it correctly launched Python 3.10.21 (`target-discovery`) every time, confirmed by checking both the notebook's resulting `language_info.version` and that `lifelines` imported successfully. All 4 notebooks now carry this same fix and were spot-checked directly (not assumed) to confirm each one's saved `language_info.version` reads `3.10.21` and its `kernelspec.name` reads `target-discovery`. Opening any of these notebooks in Jupyter or VS Code will now default to the correct environment too, since editors read this same metadata field.

**How a different environment *could* have changed results, even though it didn't here:** this is a real category of risk worth naming honestly, not just "it happened to be fine." Three distinct ways it can bite:
- **Floating-point precision differences** (what actually happened here) — different builds of numpy/scipy can round the last few decimal digits of a calculation differently. Essentially always harmless for a scientific conclusion, since nothing in this project's decisions depends on precision beyond a handful of significant figures.
- **A genuinely different algorithm or default behavior between library versions** — this is the real risk, and did *not* happen here, but could in principle: a statistical test's default parameter changing between versions, a deprecated function behaving differently, or an edge-case (empty group, NaN handling) resolving differently. This would change an actual number, not just its last digit — the kind of thing that would need investigating exactly like the pan-essential-gene or sex-confound issues earlier in this project, not assumed away.
- **A package missing entirely, causing a loud failure** — how this specific bug was actually caught (`lifelines` isn't in the base environment). This is the "good" failure mode: it's impossible to miss. The dangerous version is a package that happens to exist in *both* environments (like pandas/numpy/scipy/matplotlib here) but produces a real, silent, non-obvious behavior difference — that's the one that requires actively checking which kernel ran, rather than trusting that "it worked" means "it worked in the right place."

### Survival analysis results

Ran on the 142 TNBC patients who have both survival data and expression data, using `data_utils.get_tnbc_survival_data()` (new: builds `time`/`event` from `vital_status` + `days_to_death`/`days_to_last_followup`, plus age and a simplified I–IV tumor stage for optional Cox-model adjustment).

### Kaplan-Meier, in plain terms

Picture all 142 patients alive on day one. As time passes, some die — their line on the chart drops. Others are still alive when tracking stops ("censored") — their eventual fate is unknown, but it's known for certain they survived at least that long, and Kaplan-Meier correctly credits that partial information instead of discarding it. To test a gene, patients are split into "high expression" (above the median) and "low expression" (below it), and one survival curve is drawn per group. If the "high" curve drops noticeably faster, that's a hint the gene matters. The **log-rank test** asks whether the gap between the two curves is bigger than random chance would produce on its own.

### Cox regression, in plain terms

Instead of splitting patients into two buckets, Cox regression uses each patient's actual expression value directly and asks: for every one-unit increase in this gene's expression, how much does the risk of dying at any given moment get multiplied by? That multiplier is the **hazard ratio** — HR=1 means no effect, HR>1 means higher expression is associated with worse survival, scaling smoothly rather than lumping everyone into two buckets the way Kaplan-Meier's median split does. Running it a second time with age and tumor stage added as covariates (the "adjusted" version) answers a different question: is this really about the gene, or just that older/later-stage patients happen to express it differently? If the result holds up — or gets *stronger* — after adjusting, that's a real sign the gene itself matters rather than just riding along with age or stage.

**Kaplan-Meier (median-split, log-rank test): no gene survives FDR correction** — every corrected q-value is above 0.66. Worth naming honestly rather than downplaying: this cohort has only **21 deaths** among 142 patients, and a survival analysis's real statistical power comes from the number of *events*, not the number of patients. 21 events is a small number to detect anything short of a very large effect, especially with a median split that throws away information by collapsing a continuous expression value into two buckets.

**Cox regression (continuous expression, age/stage-adjusted) finds one real signal: `LY6E`.** Unadjusted hazard ratio 1.62 (higher expression → worse survival), p=0.019 — not quite enough to survive correction across 15 genes alone (q=0.28). But adjusting for age and tumor stage **strengthens** the result (HR 1.74, p=0.0024, **q=0.036 — survives correction**). That's a meaningful pattern: part of the crude association was being diluted by age/stage differences between patients, and controlling for them reveals a cleaner, stronger effect — the opposite of what a spurious/confounded result would do. `LY6E` now has real survival evidence from this project's own data, on top of Week 2's independent literature validation and Week 3's tumor-overexpression finding.

**`KIF2C` shows no survival association here (cox_p=0.72) — and that's expected, not a contradiction.** This lines up exactly with the HPA discrepancy investigated in Week 3: HPA's own single-cohort analysis of `KIF2C` also came back "unprognostic," while the published literature that *did* find significance pooled many independent cohorts for far more statistical power than any single cohort — this one included — can offer. A 142-patient, 21-event cohort was never likely to detect that effect alone; this null result doesn't undermine `KIF2C`'s standing, it's simply consistent with what a dataset this size can and can't show.

### What other target-discovery frameworks do about weighting — checked before deciding

Before picking a weighting scheme, looked at how the field actually handles this, since "how do others do it" is exactly the kind of question worth being able to answer in an interview. Three different philosophies show up:

- **Don't combine at all.** `shinyDepMap`, the standard tool for browsing DepMap data, deliberately does *not* build a single efficacy+selectivity score — its authors note the two axes trade off against each other (the strongest-effect genes tend to be the least selective, and vice versa), so collapsing them into one number would hide a real tension. It shows a 2D scatterplot instead and leaves the call to the researcher.
- **Filter sequentially, rank only what survives — no composite score at all.** A DepMap-based head-and-neck cancer target paper (Zhang et al., identifying `PAK2`) uses a pure pipeline: essentiality threshold → druggability filter → hard-exclude pan-essential/core-fitness genes (the same shape as this project's own Week 2 plausibility filter) → rank survivors by essentiality strength. Safety and selectivity are gates applied *before* ranking, never blended into a score.
- **Weighted combination, with the weights made explicit.** Open Targets Platform — the field's most-used target-disease association resource — does combine many evidence sources into one score, but via a documented weighted harmonic sum, and its newer "Target Prioritisation" view keeps tractability/safety as a *separate panel* shown alongside the association score rather than merged into it. A related methods paper (Kim et al., *Scientific Reports* 2019) that does build an explicit efficacy-vs-safety composite uses a genuinely equal weighted sum (0.5/0.5) as its default case study, while stating outright that the weighting is a subjective choice, not a derived constant.

The common thread: safety in particular tends to be kept out of the same score as the positive-evidence axes, whether that means a hard filter or a separate display panel. That's the precedent this project's own composite score follows.

### The composite score: rank-averaging three evidence axes, safety/druggability as annotations

Decided with the user, not unilaterally: average the ranks of the three **continuous evidence-strength axes** — essentiality (Week 2's Mann-Whitney q-value), tumor selectivity (Week 3's tumor-vs-normal q-value), and survival association (this week's age/stage-adjusted Cox q-value) — into one composite rank, equally weighted. Safety (the GTEx critical-tissue flag) and druggability (HPA protein class/subcellular location) are kept as **annotations shown next to the ranking, not folded into the score** — adjustable later if the user wants to revisit it, but the field precedent above (safety as a gate or a separate panel, not a blended score) supports this as the default.

**Why rank-average rather than average the raw q-values or z-scores:** the three axes aren't on comparable numeric scales — a q-value of 1e-58 and a Cox p-value of 0.05 aren't the same "distance" from significance, so averaging them directly would let whichever axis happens to produce more extreme numbers dominate by accident. Rank-averaging sidesteps that: each axis contributes one equally-weighted vote on relative ordering. It's also naturally more robust to the survival axis being underpowered (only 21 deaths among 142 patients) — a noisy, near-random p-value can only nudge a gene's *rank* by a little, whereas it could swing a raw z-score average by a lot.

**What the final ranking actually shows, read honestly:**
- **`IFI6` and `LY6E` come out on top (ranks 1 and 2)** — and both carry a "high" GTEx safety flag. This is the concrete payoff of the annotation-not-filter decision: a hard safety filter applied before ranking would have removed two of the top three candidates outright, on the basis of a whole-blood expression signal that's more likely a circulating-immune-cell artifact (Week 3) than evidence against these being real TNBC-cancer-cell dependencies.
- **`IFI6` edges out `LY6E`, and the reason is worth naming out loud:** rank-averaging rewards consistency across axes over one standout result. `LY6E` has this project's only statistically significant survival finding (q=0.036) but a middling tumor-selectivity rank (10th of 15), which pulls its composite down. `IFI6` is never the best on any single axis (7th/3rd/3rd) but never weak either. A scheme that weighted survival more heavily — because it's the most clinically direct signal — would put `LY6E` first instead. That's the real, defensible tradeoff of choosing equal weighting, not a hidden side effect.
- **A caution about the survival axis specifically:** only `LY6E`'s Cox result actually survives FDR correction; every other gene's adjusted q-value is above 0.4, several tied outright. A gene ranking 2nd or 3rd on survival among these 15 means "one of the least non-significant results," not a second real finding — the composite doesn't distinguish real signal from the least-noisy-looking non-effect, a genuine limitation of rank-averaging across axes with very different statistical power.
- **`KIF2C`** — despite the strongest outside literature support and the single best tumor-selectivity rank (1st) — lands mid-pack (9th, tied with `PSMD9`), pulled down by a middling essentiality rank and the weakest survival rank (consistent with the power limitation already established via the HPA discrepancy in Week 3, not a new negative finding). The composite only reflects these three specific axes; it doesn't erase the independent literature context built up earlier.

**Final output:** `data/processed/depmap_tnbc_final_ranked_targets.csv` — all 15 candidates with the composite rank, each contributing rank, and the safety/druggability annotations, sorted best-to-worst. This is the project's final ranked target list.

### Side comparison: what if safety and druggability were scored in too?

Added purely as a comparison, not a second official result — `notebooks/04_survival_analysis.ipynb`'s last section rank-averages all **five** axes instead of three, so it's visible exactly how much the ranking would shift. Safety uses the continuous `gtex_critical_tissue_max_tpm` (lower = safer = better rank, avoiding the tie-heavy 3-bucket flag); druggability uses a new 3-tier rule off HPA's `Protein class` text (FDA-approved drug target > potential drug target/membrane protein > everything else) — a much more subjective rule than the other four axes, which is itself part of the case for leaving it out of the real score.

The comparison makes the earlier argument concrete: **`LY6E` — the one candidate with real survival significance — drops from 2nd to a tie for 5th**, purely because of a safety penalty likely driven by a whole-blood immune-cell artifact rather than true risk. **`HPRT1` and `CREB3L4` jump into the top tier mainly because of tractability** (`HPRT1` is already an FDA-approved drug target despite having the *worst* essentiality rank of all 15) rather than disease evidence — a known, general risk of folding tractability into a discovery-stage score: it can reward "already easy to drug" over "best evidence for this disease." `KIF2C` does rise too, but for a better reason — a genuinely very low critical-tissue safety profile, consistent with (not contradicting) its existing literature support. `IFI6` stays #1 either way. Saved to `data/processed/depmap_tnbc_5axis_comparison.csv`, kept separate from the primary result file.

### Column glossary for the final tables

Both `depmap_tnbc_final_ranked_targets.csv` and `depmap_tnbc_5axis_comparison.csv` accumulate columns from every week — worth a plain-language reference rather than re-deriving what each one means from the column name alone. Using `IFI6`'s actual row as a running example (`effect_size`=-0.10, `u_q`=0.123, `log2fc_tumor_vs_normal`=+2.32, `gtex_critical_tissue_max_tpm`=71.7, `safety_flag`="high"):

**Essentiality (Week 2) — is this gene needed for TNBC cells, and is that TNBC-specific?**
- `effect_size`: mean Chronos score in the 25 TNBC lines minus the mean in the 1,181 other lines. Chronos ≈0 = no growth effect on knockout, ≈-1 = as essential as a typical pan-essential gene. More negative = more essential in TNBC.
- `t_p`/`u_p`: raw p-values, Welch's t-test / Mann-Whitney U (the primary test) comparing those two groups.
- `n_tnbc`/`n_other`: group sizes for that test (25 / 1,181, same for every gene).
- `t_q`/`u_q`: those p-values after genome-wide BH-FDR correction. `u_q` built the original shortlist.
- `pan_cancer_mean_effect`: this gene's mean Chronos score across *every* DepMap line, any cancer type — the pan-essential/housekeeping-gene filter (excluded below -1.0).
- `median_log2_rsem_tnbc_tumor`: median log2(RSEM+1) expression in **TNBC-only** tumor samples from TCGA — the "is this actually on in real tumors" gate (required >1.0).

**Tumor selectivity (Week 3) — is it turned up in tumor vs. normal breast?**
- `median_log2_tumor`/`median_log2_normal_breast`: median log2(RSEM+1) expression across **all** TCGA-BRCA tumor samples (1,093 — the whole BRCA cohort, deliberately not TNBC-only, for more power) vs. all matched-normal breast samples (112). Don't read "tumor" here as "TNBC tumor" the way the essentiality column above is — different population, on purpose.
- `log2fc_tumor_vs_normal`: the difference of those two medians; positive = higher in tumor.
- `tumor_vs_normal_p`/`_q`: Mann-Whitney p-value / BH-q-value for that comparison.

**Safety (Week 3) — could hitting this gene hurt healthy tissue?**
- `gtex_critical_tissue_max_tpm`: the highest median TPM this gene reaches across four "vital organ" GTEx tissues (heart left ventricle, heart atrial appendage, liver, whole blood as a bone-marrow proxy).
- `safety_flag`: that number bucketed — <5 low, 5–20 moderate, >20 high (documented judgment call, not derived).

**HPA annotations (Week 3) — druggability/prognostic context**
- `Protein class`: HPA's own tags (subcellular class, known drug-target status, etc.), comma-separated when several apply.
- `Subcellular main location`: HPA's predicted/observed compartment — can look slightly in tension with `Protein class` (e.g. tagged "membrane protein" but localized to "Mitochondria" — that class doesn't always mean *plasma* membrane).
- `Cancer prognostics - Breast Invasive Carcinoma (TCGA)`/`(validation)`: HPA's own precomputed survival call in two cohorts, formatted `"{prognostic/unprognostic} (p-value)"`. Their bar for "prognostic" is p<0.001, stricter than ordinary significance (see the HPA section above).

**Legacy rank columns from narrowing 20→15, before survival testing — a different rank system than the final ones below, easy to confuse by name**
- `rank_essential`/`rank_tumor`: rank by `u_q`/`tumor_vs_normal_q`, computed across the **20** genes that passed the log2fc>0 filter (not these 15) — only ever used to pick which 15 genes got survival-tested.
- `combined_rank`: the plain sum `rank_essential + rank_tumor` — what actually picked the top 15. Fully superseded by `composite_rank` below.

**Survival (Week 4)**
- `n_patients`: how many of the 142 evaluable patients had a usable value for that specific test (sometimes 139 for Cox, if age/stage was missing).
- `logrank_p`/`logrank_q`: Kaplan-Meier median-split log-rank test, raw and FDR-corrected.
- `hazard_ratio`/`cox_p`: unadjusted Cox regression hazard ratio (per 1-unit log2-expression increase) and its p-value; HR>1 = higher expression, worse survival.
- `hazard_ratio_adj`/`cox_p_adj`: the same Cox model with age and tumor stage added as covariates.
- `cox_q`/`cox_q_adj`: BH-FDR-corrected versions, across all 15 genes. `cox_q_adj` is the project's primary survival metric.

**The primary composite score (this week)**
- `rank_essentiality`/`rank_tumor_selectivity`/`rank_survival`: rank by `u_q`/`tumor_vs_normal_q`/`cox_q_adj`, recomputed fresh across just these **15** genes (distinct from `rank_essential`/`rank_tumor` above).
- `composite_rank`: the plain average of those three ranks. Lower = better — the project's real answer.

**The 5-axis side comparison**
- `rank_safety`: rank by `gtex_critical_tissue_max_tpm`, ascending (lower TPM = safer = better rank).
- `druggability_tier`: 1/2/3 bucket (1 = FDA-approved drug target, 2 = potential target or membrane protein, 3 = everything else).
- `rank_druggability`: rank of that tier (expect ties — it's a coarse 3-level scale).
- `composite_rank_5axis`: average of all five ranks. Comparison-only, not the project's answer.

**Week 4 outcome:** Complete. Kaplan-Meier and Cox survival analysis, plus a composite score combining essentiality, tumor selectivity, and survival (safety/druggability as annotations), producing a final ranked list of the 15 candidates. `LY6E` has the strongest individual statistical evidence; `IFI6` ranks first under equal-weighted rank-averaging because it's consistently solid across all three axes rather than a standout on one.

## Week 5: Explain and polish the result

- [ ] Select one or two leading targets for a literature and druggability case study.
- [ ] Describe the next experimental validation step.
- [ ] Write the README using the project story and results recorded here.
- [ ] Add a summary visualization.
- [ ] Pin the environment and clean the notebooks.
- [ ] Build the optional Streamlit explorer if time allows.

**Week 5 outcome:** A reproducible portfolio project with a clear scientific narrative and defensible conclusions.
