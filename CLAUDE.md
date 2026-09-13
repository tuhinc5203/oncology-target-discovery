# Assistant Project Tracker

This file is internal working context for the coding assistant. Keep it concise, operational, and more technical than `NOTES.md`. Do not treat it as the user-facing project narrative.

## Workspace state

- Workspace: `oncology-target-discovery`
- Current artifacts: `oncology-target-discovery-project-plan.md`, `NOTES.md`, `CLAUDE.md`, `environment.yml`, `.gitignore`
- Git repository initialized (branch `main`, first commit made 2026-09-13). Safe to use normal git commands now.
- Local conda environment `target-discovery` (Python 3.10) created with pandas, numpy, scipy, matplotlib, seaborn, lifelines, jupyter, ipykernel. Jupyter kernel registered as "Python (target-discovery)". Exact versions pinned in `environment.yml`.
- Directory layout: `data/raw/{depmap,tcga,gtex,hpa}/` (untracked except `.gitkeep`, for original downloads), `data/processed/` (untracked except `.gitkeep`, for cleaned/intermediate data), `notebooks/`, `src/` — all currently empty scaffolding.
- No datasets downloaded yet.

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

- Week 0 TNBC decision is complete.
- Documentation has been created and validated.
- Python environment, Jupyter kernel, and git repository are set up (2026-09-13).
- Data acquisition has not started. Blocked on the user, but only for browser access, not an account: DepMap's public data (Chronos CRISPR scores, cell line metadata) requires no registration/login — a direct API request from this environment hit a Cloudflare bot-check page, which a normal browser passes automatically. There is no sign-up flow to look for. The user needs to download `CRISPRGeneEffect.csv` + `Model.csv` from depmap.org/portal/download/ (or the "All Data"/"Custom Downloads" tab) into `data/raw/depmap/`.
- As of the 25Q2 release, DepMap no longer bulk-publishes to Figshare; files come from the portal's download tabs directly.
- No technical assumptions about exact DepMap release, TCGA subtype field, or TNBC cell-line mapping have been confirmed yet.

## Resume procedure

1. Read this file, `NOTES.md`, and the relevant Week 0/Week 1 section of the project plan.
2. Check whether the user has downloaded DepMap files or provided access details.
3. Establish the local Python environment before writing analysis code.
4. Inspect real file schemas before choosing loaders or subtype filters.
5. Record dataset release/date and mapping decisions in both code metadata and the user's results log.
6. After each meaningful milestone, update the completed task in `NOTES.md` and the implementation state here.

## Technical guardrails

- Prefer small, reproducible modules over notebook-only logic.
- Preserve raw downloads separately from cleaned/intermediate data.
- Record missingness, sample counts, identifiers, and filtering decisions.
- Use multiple-testing correction for genome-wide comparisons.
- Validate candidate rankings against known TNBC biology before presenting novel hypotheses.
- Do not claim a target is validated; this project produces computational prioritization for follow-up experiments.

## Open decisions

- Exact DepMap release and file names.
- Source and rules for mapping DepMap breast cancer cell lines to TNBC.
- TCGA-BRCA subtype field and the operational TNBC inclusion rule.
- Whether matched TCGA normal samples are sufficient or GTEx is the primary normal baseline.
- Statistical test, effect-size definition, and composite-score weights.
