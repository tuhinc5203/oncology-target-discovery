# Assistant Project Tracker

This file is internal working context for the coding assistant. Keep it concise, operational, and more technical than `NOTES.md`. Do not treat it as the user-facing project narrative.

## Workspace state

- Workspace: `oncology-target-discovery`
- Current artifacts: `oncology-target-discovery-project-plan.md`, `NOTES.md`, `CLAUDE.md`, `environment.yml`, `.gitignore`, `src/data_utils.py`, `scripts/download_tcga.py`, `scripts/download_gtex.py`.
- Git repository initialized (branch `main`) and pushed to `https://github.com/tuhinc5203/oncology-target-discovery` (`origin/main` tracked). Safe to use normal git commands, including push.
- Local conda environment `target-discovery` (Python 3.10) created with pandas, numpy, scipy, matplotlib, seaborn, lifelines, jupyter, ipykernel. Jupyter kernel registered as "Python (target-discovery)". Exact versions pinned in `environment.yml`.
- Directory layout: `data/raw/{depmap,tcga,gtex,hpa}/` (untracked except `.gitkeep`, for original downloads), `data/processed/` (untracked except `.gitkeep`, for cleaned/intermediate data), `notebooks/`, `src/`, `scripts/`.
- `data/raw/depmap/` populated: `Model Data.csv` (2,154 × 49) and `CRISPR Gene Effect.csv` (1,208 cell lines × ~18,531 genes), DepMap Public **26Q1**.
- `data/raw/tcga/` populated: `BRCA.rnaseqv2_RSEM_genes_normalized.data.txt` (20,531 genes × 1,212 samples), `All_CDEs.txt` (131 attrs × 1,097 patients, has ER/PR/HER2 IHC/FISH status), `BRCA.clin.merged.picked.txt` (survival fields). Source: GDAC Firehose `stddata__2016_01_28` BRCA run. Downloaded via `scripts/download_tcga.py` (verified byte-identical on a fresh run — no bot-check on this host, unlike DepMap).
- `data/raw/gtex/` populated: `GTEx_Analysis_v11_gene_median_tpm.gct.gz` (74,628 genes × 68 tissues), GTEx **v11**. Downloaded via `scripts/download_gtex.py` (public GCS bucket, no auth).
- HPA not downloaded yet (optional, Week 3).

## User-facing source of truth

- `NOTES.md` is for the user: plain-language catch-up, weekly tasks, decisions, outcomes, and material that can later become `README.md`.
- `oncology-target-discovery-project-plan.md` is the detailed reference plan.
- Keep implementation details, unresolved choices, and assistant resume state here instead of cluttering `NOTES.md`.

## Scientific scope

- Disease focus: TNBC.
- Public sources: DepMap Chronos, TCGA-BRCA, GTEx, and optionally Human Protein Atlas.
- TNBC must be defined explicitly in both cell-line and patient analyses. Never silently substitute all breast cancer for TNBC.
- Prior Oxford BioTherapeutics experience is context only. Never request, infer, or record proprietary targets, results, methods, or confidential information.

## Current implementation state

- Week 0 is complete: TNBC decision recorded, environment/kernel/git set up, DepMap files downloaded and inspected (26Q1 release — see below).
- DepMap's public data (Chronos CRISPR scores, cell line metadata) requires no account; downloaded directly from the portal's "All Data"/"Custom Downloads" tabs (no longer bulk-published to Figshare as of 25Q2).
- **DepMap TNBC cell-line mapping resolved:** `Model Data.csv`'s `ModelSubtypeFeatures` column directly labels molecular subtype (e.g. `basal_A TNBC`, `luminal TNBC`, `TNBC`) for most `OncotreeLineage == "Breast"` rows. Filtering for substring `"TNBC"` gives 34 of 96 breast cell lines; 25 of those have CRISPR data in `CRISPR Gene Effect.csv`. 15 breast lines have no `ModelSubtypeFeatures` value — treat as unknown, exclude from both TNBC and non-TNBC comparison groups, don't default them to "non-TNBC." No manual receptor-status mapping needed. Full reasoning in `NOTES.md`'s "Defining the TNBC cell-line set" section.
- **TCGA-BRCA TNBC patient mapping resolved:** `data_utils.get_tnbc_patient_barcodes()` combines `breast_carcinoma_estrogen_receptor_status`, `..._progesterone_receptor_status`, and HER2 IHC (`lab_proc_her2_neu_immunohistochemistry_receptor_status`) + FISH (`lab_procedure_her2_neu_in_situ_hybrid_outcome_type`) from `All_CDEs.txt`. HER2-negative = IHC negative, OR IHC equivocal with FISH negative (ASCO/CAP reflex rule). TNBC = ER-neg AND PR-neg AND HER2-neg; missing/indeterminate on any marker excludes the patient from both groups. Result: 143/1,097 patients (13%, matches expected clinical prevalence), 142 with matched tumor expression data. Full reasoning in `NOTES.md`'s "Defining TCGA-BRCA's TNBC patient set" section.
- **`src/data_utils.py` now has loaders for all 3 downloaded sources:** `load_model_metadata`/`load_gene_effect`/`get_tnbc_model_ids` (DepMap), `load_tcga_expression`/`load_tcga_clinical_cdes`/`get_tnbc_patient_barcodes`/`tcga_patient_barcode`/`tcga_is_tumor_sample` (TCGA), `load_gtex_median_tpm` (GTEx). All verified against the real files.
- **Week 1 is complete.** `notebooks/01_data_eda.ipynb` executed end-to-end (via `jupyter nbconvert --execute`, no errors): dimensions/missingness/distributions for all 3 downloaded sources + the clinical CDE table. Key numbers: DepMap 3.96% missing (concentrated in ~8% of genes); TCGA expression 0% missing, heavily right-skewed (log2(x+1) planned); GTEx 0% missing, 54% exact zeros. Full findings + explanations in `NOTES.md`'s "EDA findings worth remembering" section. TCGA matched-normal-vs-GTEx-baseline decision still open (1,093 tumor vs. 119 normal/other samples in the expression matrix).
- **Week 2 essentiality analysis done (biology sanity-check still pending).** `notebooks/02_selective_essentiality.ipynb` runs Welch's t-test AND Mann-Whitney U per gene (25 TNBC lines vs. 1,181 other DepMap lines with CRISPR data; 2 unknown-subtype breast lines excluded from both groups), with BH-FDR correction (`scipy.stats.false_discovery_control`) on each test separately. Results: `data/processed/depmap_tnbc_essentiality.csv` (all ~17,900 testable genes) and `data/processed/depmap_tnbc_shortlist.csv` (top 40 by Mann-Whitney q-value, effect_size < 0). Tests correlate strongly overall (Spearman ρ=0.87) but only 40% overlap in genes called significant at q<0.10 (8 vs. 13 genes) — **using Mann-Whitney's ranking as primary**, per the group-imbalance reasoning in `NOTES.md`. Full write-up in `NOTES.md`'s "Choosing the essentiality test" section. **Not yet done:** checking the shortlist against known TNBC biology (plan's Week 2 step 5, and this file's own "validate against known biology" guardrail) — do NOT present these genes as findings until that check happens.
- **Local dev gotcha:** `conda activate target-discovery` doesn't reliably win the `PATH` race against Homebrew's system Python in this shell — call the env's Python by full path (`/Applications/miniconda3/envs/target-discovery/bin/python3`) to avoid silently running without the installed packages.
- **Bot-check pattern, confirmed twice now:** DepMap's portal blocks automated requests (Cloudflare) even though no login is actually required. TCGA/GTEx don't have this — GDAC Firehose and GTEx's GCS bucket are plain public HTTP with no bot-check, so those two are scripted (`scripts/download_tcga.py`, `scripts/download_gtex.py`), while DepMap stays a manual step. Don't assume a data portal is blocked just because DepMap was — test each one directly (`curl`/`WebFetch`) before concluding it needs the user's browser.

## Resume procedure

1. Read this file, `NOTES.md`, and the relevant Week 0/Week 1 section of the project plan.
2. Check whether the user has downloaded DepMap files or provided access details.
3. Establish the local Python environment before writing analysis code.
4. Inspect real file schemas before choosing loaders or subtype filters.
5. Record dataset release/date and mapping decisions in both code metadata and `NOTES.md`'s "Technical concepts & decisions" section.
6. After each meaningful milestone, update the completed task in `NOTES.md` and the implementation state here.

## Technical guardrails

- Prefer small, reproducible modules over notebook-only logic.
- Preserve raw downloads separately from cleaned/intermediate data.
- `data/processed/` is gitignored by default (like `data/raw/`), but small, meaningful, named result files worth tracking in git history (e.g. a shortlist CSV a later week's analysis depends on) get `git add -f`'d individually rather than left uncommitted — same treatment as the `.gitkeep` placeholders. Don't force-add large/disposable intermediate caches this way.
- Record missingness, sample counts, identifiers, and filtering decisions.
- Use multiple-testing correction for genome-wide comparisons.
- Validate candidate rankings against known TNBC biology before presenting novel hypotheses.
- Do not claim a target is validated; this project produces computational prioritization for follow-up experiments.

## Open decisions

- Whether matched TCGA normal samples (only ~119 of 1,212 samples aren't primary-tumor-coded) are sufficient or GTEx is the primary normal baseline for Week 3's safety filtering.
- Composite-score weights (Week 4).
- Whether the Week 2 shortlist survives the pending known-biology sanity check, or needs revisiting.

## Resolved decisions

- **DepMap release:** Public 26Q1 (`Model Data.csv`, `CRISPR Gene Effect.csv`).
- **DepMap TNBC cell-line mapping:** substring match on `ModelSubtypeFeatures` containing `"TNBC"`, among `OncotreeLineage == "Breast"` rows. 34 lines match; 25 have CRISPR data.
- **TCGA-BRCA run:** GDAC Firehose `stddata__2016_01_28` (BRCA) — same source as cBioPortal's `brca_tcga` study.
- **TCGA-BRCA TNBC patient mapping:** ER-neg AND PR-neg AND combined-HER2-neg (IHC negative, or IHC equivocal + FISH negative), via `get_tnbc_patient_barcodes()`. 143/1,097 patients; 142 with expression data.
- **GTEx release:** v11 (`GTEx_Analysis_v11_gene_median_tpm.gct.gz`, 74,628 genes × 68 tissues).
- **Essentiality test + effect size:** mean-difference effect size; Mann-Whitney U as primary test (t-test kept alongside for comparison) — see `NOTES.md`.
