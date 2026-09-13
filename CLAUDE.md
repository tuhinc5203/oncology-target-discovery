# Assistant Project Tracker

This file is internal working context for the coding assistant. Keep it concise, operational, and more technical than `NOTES.md`. Do not treat it as the user-facing project narrative.

## Workspace state

- Workspace: `oncology-target-discovery`
- Current artifacts: `oncology-target-discovery-project-plan.md`, `NOTES.md`, `CLAUDE.md`, `environment.yml`, `.gitignore`
- Git repository initialized (branch `main`, first commit made 2026-09-13). Safe to use normal git commands now.
- Local conda environment `target-discovery` (Python 3.10) created with pandas, numpy, scipy, matplotlib, seaborn, lifelines, jupyter, ipykernel. Jupyter kernel registered as "Python (target-discovery)". Exact versions pinned in `environment.yml`.
- Directory layout: `data/raw/{depmap,tcga,gtex,hpa}/` (untracked except `.gitkeep`, for original downloads), `data/processed/` (untracked except `.gitkeep`, for cleaned/intermediate data), `notebooks/`, `src/`.
- `data/raw/depmap/` populated (2026-09-13): `Model Data.csv` (2,154 rows × 49 cols) and `CRISPR Gene Effect.csv` (1,208 cell lines × ~18,531 genes), DepMap Public **26Q1** release. TCGA/GTEx/HPA not downloaded yet.

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
- Week 1 not started: DepMap gene-effect matrix not yet loaded/cleaned in code, TCGA-BRCA and GTEx not yet downloaded, TCGA subtype field/inclusion rule still undecided.
- **Local dev gotcha:** `conda activate target-discovery` doesn't reliably win the `PATH` race against Homebrew's system Python in this shell — call the env's Python by full path (`/Applications/miniconda3/envs/target-discovery/bin/python3`) to avoid silently running without the installed packages.

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
- Record missingness, sample counts, identifiers, and filtering decisions.
- Use multiple-testing correction for genome-wide comparisons.
- Validate candidate rankings against known TNBC biology before presenting novel hypotheses.
- Do not claim a target is validated; this project produces computational prioritization for follow-up experiments.

## Open decisions

- TCGA-BRCA subtype field and the operational TNBC inclusion rule.
- Whether matched TCGA normal samples are sufficient or GTEx is the primary normal baseline.
- Statistical test, effect-size definition, and composite-score weights.

## Resolved decisions

- **DepMap release:** Public 26Q1 (`Model Data.csv`, `CRISPR Gene Effect.csv`).
- **DepMap TNBC cell-line mapping:** substring match on `ModelSubtypeFeatures` containing `"TNBC"`, among `OncotreeLineage == "Breast"` rows. 34 lines match; 25 have CRISPR data.
