# Week 5 case study: literature and druggability research

Background material for the README's case-study section on the four Week 5 targets
(`IFI6`, `LY6E`, `HPRT1`, `KIF2C`). This file is working research — the actual case-study
prose belongs in the README. The "next experimental step" for each gene is left blank
deliberately: that's the one section meant to be written in your own words, tying back
to real bench experience, not pulled from a literature search.

All findings below are from web literature search done 2026-09-17, not from memory —
same standard as the Week 2/3 literature checks in `NOTES.md`.

---

## `IFI6`

**What it is:** Interferon alpha-inducible protein 6 (aka `G1P3`), an interferon-stimulated
gene. Localizes to the **inner mitochondrial membrane** — not the plasma membrane, despite
HPA's generic `Protein class` label of "Predicted membrane proteins" in this project's own
table. Functions as an anti-apoptotic, pro-proliferative factor by stabilizing mitochondrial
function and suppressing mitochondrial ROS accumulation.

**Breast cancer literature — high expression, worse outcomes, but not TNBC-specific:**
- [Cheriyath et al., *Br J Cancer* 2018](https://www.nature.com/articles/s41416-018-0137-3) — `IFI6`/`G1P3` (mitochondrial, anti-apoptotic) promotes metastatic potential of breast cancer cells through mitochondrial ROS suppression; associated with poor distant-metastasis-free survival.
- [Bioinformatics analysis, *Sci Rep* 2025](https://www.nature.com/articles/s41598-025-20489-6) ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12534504/)) — `IFI6` upregulated in breast cancer overall, correlates with poor OS/RFS specifically in **ER-positive, PR-positive, HER2-positive, and node-positive** subtypes. Immune correlations: positive with Tregs and M1 macrophages, negative with naive B/plasma cells — interpreted as tumor-cell-driven immune microenvironment shaping. **Explicitly states no significant association was found between `IFI6` expression and TNBC subtype.**
- `IFI6` is also a direct target of estrogen signaling and is linked to tamoxifen resistance — mechanistically ER-pathway-dependent, which is by definition not present in TNBC.
- [Esophageal squamous cell carcinoma, *J Exp Clin Cancer Res* 2020](https://jeccr.biomedcentral.com/articles/10.1186/s13046-020-01646-3) — `IFI6` knockdown (not just correlation) causes ROS accumulation via mitochondrial dysfunction and ER stress, inhibiting tumor progression. Mechanistically consistent with the breast cancer findings above, in a different tissue.

**Worth stating plainly in the case study, not glossed over:** this project ranks `IFI6` #1
using TNBC-specific evidence (TNBC-vs-other-lineage essentiality, TNBC-tumor-vs-normal
expression, TNBC-patient survival). The largest available published analysis of `IFI6` in
breast cancer found the opposite subtype pattern — its prognostic signal concentrates in
hormone-receptor-positive/HER2+ disease, and explicitly *not* TNBC. This doesn't invalidate
this project's result (different method, TNBC-only comparison vs. pan-subtype study, and the
published paper is correlational bulk-tumor RNA-seq while this project also has an
independent CRISPR-dependency axis the published paper doesn't), but it's a genuine, named
gap between this project's convergent internal evidence and the external TNBC-subtype
literature — the same kind of discrepancy Week 3 handled explicitly for `KIF2C`/HPA, not one
to pick around.

**Druggability:** no approved or clinical-stage `IFI6`-targeted drug found. Inner-mitochondrial-membrane
localization rules out a straightforward antibody/surface-target approach despite HPA's
generic "membrane protein" label. The 2025 *Sci Rep* paper speculates about `IFI6` inhibition
combined with PD-1/PD-L1 blockade, but flags this as untested.

**Next experimental step:** _(fill in — your own words, tied to your bench experience)_

---

## `LY6E`

Already substantially covered in Weeks 2–3 (`NOTES.md` lines ~143, ~149, ~226, ~282) — recapped
here for completeness, not re-researched:

- Independently published (2025) as a TNBC-specific "theranostic target": high membrane
  expression specifically in TNBC cell lines, low in normal breast epithelium, confirmed in a
  xenograft model, significantly elevated in TNBC tissue (p<0.0001) — a different method
  entirely (RNA-seq + protein + xenograft) from this project's DepMap/TCGA/GTEx pipeline,
  making it the project's clearest case of independently recovering known biology.
- This project's own Cox regression: the only candidate whose survival association survives
  FDR correction (HR 1.74, q=0.036, age/stage-adjusted) — strengthened, not weakened, by
  adjustment.
- HPA: `Predicted membrane proteins` — genuinely surface-accessible, consistent with the
  published "membrane expression" description above.
- Real caveat carried from Week 3: high whole-blood expression (175.5 TPM, "high" safety
  flag) — `LY6E` is an interferon-stimulated gene broadly expressed in circulating immune
  cells, so this is plausibly a circulating-immune-cell artifact rather than a true
  on-target liability, but it isn't resolved, just annotated.

**Next experimental step:** _(fill in — your own words, tied to your bench experience)_

---

## `HPRT1`

**What it is:** Hypoxanthine-guanine phosphoribosyltransferase, the purine salvage pathway
enzyme that converts hypoxanthine/guanine + PRPP into IMP/GMP for nucleotide synthesis.
Complete loss causes Lesch-Nyhan syndrome.

**Correction to an earlier note in this project (CLAUDE.md/NOTES.md said HPRT1 "is already
an FDA-approved drug target (allopurinol, for gout)" — this is wrong and worth fixing:**
allopurinol's pharmacological target is **xanthine oxidase**, a different enzyme entirely; it
has no direct inhibitory relationship to `HPRT1`. What HPA's "FDA approved drug targets"
protein-class label is actually picking up on: `HPRT1` is the enzyme that metabolically
**activates** the thiopurine prodrugs **6-mercaptopurine, 6-thioguanine, and azathioprine**
(all FDA-approved — used in acute lymphoblastic leukemia and, for azathioprine,
transplant/IBD immunosuppression) into their cytotoxic thioguanine-nucleotide form. `HPRT1`
is required for these drugs to work; no approved drug inhibits `HPRT1` itself. That's a
meaningfully different and more precise story than "already druggable" — worth making
explicit in the case study rather than repeating the shorthand.
([DrugBank: Mercaptopurine](https://go.drugbank.com/drugs/DB01033), [DrugBank: Allopurinol](https://go.drugbank.com/drugs/DB00437))

**Cancer biology — real oncogenic role, and one genuinely TNBC-specific hit:**
- [Pan-cancer prognostic/immunological analysis, 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10950352/) — `HPRT1` RNA "significantly elevated... particularly in basal cells and **triple-negative breast cancer**" vs. normal tissue; validated against an independent TNBC dataset (GSE107764) for a `HPRT1`–PD-L1/PD-1 correlation. High expression associated with worse OS in several cancer types (HNSC, KIRP, MESO, PRAD, UCEC, UCS — breast cancer's own direction not confirmed in what this search returned; don't overclaim it). This is the most directly TNBC-specific literature hit of the three genes in this file — stronger, in that narrow sense, than what turned up for `IFI6`.
- [HIF-1α–`HPRT1` axis, EGFR-mutant lung adenocarcinoma, 2024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11441087/) — HIF-1α transcriptionally activates `HPRT1` to sustain purine metabolism and tumor growth, and contributes to gefitinib resistance. Direct mechanistic (not just correlational) evidence of an oncogenic role, in a different cancer type.
- [Electron-transport-chain (ETC) inhibition and purine salvage, *Cell Metab* 2024](https://www.cell.com/cell-metabolism/fulltext/S1550-4131(24)00190-6) — under mitochondrial ETC dysfunction, cells become dependent on purine salvage, and `HPRT1` specifically becomes conditionally essential; an unbiased CRISPR screen in pancreatic cancer cells found `HPRT1` (and the transporter `SLC29A1`) conditionally essential during ETC blockade. **Blocking `HPRT1` sensitizes cancer cells to ETC inhibition** — a real combination-therapy angle.

**Worth naming as a tension, not smoothed over:** this project's own CRISPR essentiality data
ranks `HPRT1` **worst (15th of 15)** on essentiality among the shortlisted candidates — TNBC
lines aren't strongly dependent on it in unperturbed culture. The ETC-inhibition literature
above offers a plausible reconciliation: `HPRT1` may be *conditionally* essential (dependent
on mitochondrial/metabolic stress state) rather than broadly essential, which a standard,
unperturbed DepMap CRISPR screen wouldn't necessarily surface as a strong dependency. That's
a hypothesis this project's data can't itself confirm — flag it as one, not as settled.

**Druggability:** no approved or clinical direct `HPRT1` inhibitor for oncology found. The
concrete druggability angle here is a repurposing/combination story (existing thiopurine
pharmacology; or ETC-inhibitor co-treatment), not "already has an approved inhibitor" —
exactly the nuance the correction above is trying to capture. Good case-study material
specifically *because* it shows a druggability-tier label ("FDA approved drug target") can
overstate tractability if taken at face value — a useful companion point to Week 3/4's
recurring theme of not trusting a single label without checking what it actually means.

**Next experimental step:** _(fill in — your own words, tied to your bench experience)_

---

## `KIF2C` — added as a fourth target

Not part of this project's own final 15-candidate ranking's top 3 (9th by composite score,
per `NOTES.md` line ~306), but added to the case study on further review of the Week 2
essentiality filter: that filter only ever tested *differential* essentiality (TNBC vs.
other DepMap lines, via the Mann-Whitney/t-test effect size), and never separately checked
whether a gene's *absolute* dependency in TNBC lines was actually strong. Rechecking the
final 15 candidates' own median Chronos effect within this project's 25-line TNBC set:

| Gene | Median Chronos effect (25 TNBC lines) | % of lines dependent (≤ -0.30) |
|---|---|---|
| `KIF2C` | **-0.487** | **80%** |
| `IFI6` | -0.046 | 4% |
| `LY6E` | -0.037 | 12% |
| `HPRT1` | -0.030 | 4% |

`KIF2C` has by far the strongest real, absolute CRISPR dependency of the shortlist — TNBC
lines are actually reliant on it for survival, not just relatively more reliant on it than
other lineages. `IFI6`, `LY6E`, and `HPRT1` all show weak absolute dependency by this same
check. That doesn't invalidate them (their case rests on tumor-overexpression, survival, or
literature evidence, not primarily on essentiality), but it does mean `KIF2C` is the one
candidate in the shortlist that combines *both* relative selectivity and outright, measured
dependency — a good reason to include it alongside the other three, not instead of them.

**Already substantially researched in Weeks 2–3** (`NOTES.md` lines ~210–226, ~284, ~306) —
recapped, not re-searched:
- Four independent lines of evidence converge: DepMap essentiality signal, TCGA tumor
  overexpression (log2fc, strongest tumor-selectivity rank of all 15 candidates), independent
  published literature (breast-cancer overexpression/poor-prognosis association), and — once
  the apparent HPA conflict was investigated rather than accepted at face value — HPA's own
  survival data too (p=0.0164 in HPA's validation cohort, real but below HPA's strict genome-wide
  p<0.001 cutoff, not "no association").
- No survival signal in *this project's own* 142-patient Cox model (p=0.72) — expected, not
  contradictory: a single ~21-event cohort was never powered to detect what only pooled
  multi-cohort meta-analyses found.
- Druggability: `Predicted intracellular proteins` (nuclear, kinesin motor protein) — no
  surface/antibody route, but a real small-molecule precedent exists in the same protein
  family (KIF11/Eg5 inhibitors reached clinical trials for a related kinesin).

**Next experimental step:** _(fill in — your own words, tied to your bench experience)_
