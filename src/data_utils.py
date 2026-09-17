"""Loaders for this project's raw data sources.

DepMap Public 26Q1, TCGA-BRCA (GDAC Firehose stddata__2016_01_28),
GTEx v11, and HPA (Human Protein Atlas) 25.1 are all downloaded.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPMAP_DIR = PROJECT_ROOT / "data" / "raw" / "depmap"
TCGA_DIR = PROJECT_ROOT / "data" / "raw" / "tcga"
GTEX_DIR = PROJECT_ROOT / "data" / "raw" / "gtex"
HPA_DIR = PROJECT_ROOT / "data" / "raw" / "hpa"

DEPMAP_RELEASE = "26Q1"
TCGA_RUN = "GDAC Firehose stddata__2016_01_28 (BRCA)"
GTEX_RELEASE = "v11"
HPA_RELEASE = "25.1"


def load_model_metadata(path=DEPMAP_DIR / "Model Data.csv"):
    """Load DepMap cell line/model metadata, indexed by ModelID."""
    return pd.read_csv(path, index_col="ModelID")


def load_gene_effect(path=DEPMAP_DIR / "CRISPR Gene Effect.csv"):
    """Load the Chronos CRISPR gene-effect matrix (cell lines x genes).

    Column labels are stripped down to bare gene symbols, dropping the
    trailing " (<Entrez ID>)" DepMap ships them with. Missing values
    (a gene not screened/QC-passed in a given cell line) are left as
    NaN rather than imputed here -- how to handle them is an
    analysis-time decision, not a loading-time one.
    """
    df = pd.read_csv(path, index_col=0)
    df.index.name = "ModelID"
    df.columns = [col.split(" (")[0] for col in df.columns]
    return df


def get_tnbc_model_ids(model_df):
    """ModelIDs of breast cell lines whose ModelSubtypeFeatures marks them TNBC.

    See NOTES.md's "Defining the TNBC cell-line set" for the reasoning:
    a substring match on ModelSubtypeFeatures (values like "basal_A TNBC",
    "luminal TNBC", "TNBC") among OncotreeLineage == "Breast" rows.
    """
    breast = model_df[model_df["OncotreeLineage"] == "Breast"]
    is_tnbc = breast["ModelSubtypeFeatures"].fillna("").str.contains("TNBC")
    return breast.index[is_tnbc]


def load_tcga_expression(path=TCGA_DIR / "BRCA.rnaseqv2_RSEM_genes_normalized.data.txt"):
    """Load the TCGA-BRCA RSEM-normalized expression matrix (genes x samples).

    Row index is "<gene_symbol>|<Entrez ID>" as shipped (some symbols are
    literally "?" where no gene symbol is annotated). Column labels are
    full TCGA sample barcodes, e.g. "TCGA-3C-AAAU-01A-11R-A41B-07" -- use
    `tcga_patient_barcode()` and `tcga_is_tumor_sample()` to work with them.
    """
    return pd.read_csv(path, sep="\t", index_col=0, skiprows=[1])


def tcga_patient_barcode(sample_barcode):
    """"TCGA-3C-AAAU-01A-11R-A41B-07" -> "tcga-3c-aaau" (matches clinical file columns)."""
    return "-".join(sample_barcode.split("-")[:3]).lower()


def tcga_is_tumor_sample(sample_barcode):
    """True if a TCGA sample barcode's sample-type code marks it a primary tumor ("01")."""
    return sample_barcode.split("-")[3].startswith("01")


def load_tcga_clinical_cdes(path=TCGA_DIR / "All_CDEs.txt"):
    """Load the full TCGA-BRCA clinical CDE table (attributes x patients, lowercase barcodes)."""
    return pd.read_csv(path, sep="\t", index_col=0)


def get_tnbc_patient_barcodes(cde_df):
    """Lowercase patient barcodes (e.g. "tcga-3c-aaau") classified TNBC.

    TNBC = ER-negative AND PR-negative AND HER2-negative, the standard
    clinical (IHC/FISH) definition -- see NOTES.md's "Defining TCGA-BRCA's
    TNBC patient set" for the full reasoning. HER2 status combines the IHC
    and FISH/ISH calls per the ASCO/CAP reflex-testing algorithm (an
    equivocal IHC 2+ call falls back to the FISH result). Patients missing
    or indeterminate on any of the three markers are excluded rather than
    defaulted to non-TNBC.
    """
    er = cde_df.loc["breast_carcinoma_estrogen_receptor_status"]
    pr = cde_df.loc["breast_carcinoma_progesterone_receptor_status"]
    her2_ihc = cde_df.loc["lab_proc_her2_neu_immunohistochemistry_receptor_status"]
    her2_fish = cde_df.loc["lab_procedure_her2_neu_in_situ_hybrid_outcome_type"]

    her2_negative = (her2_ihc == "negative") | ((her2_ihc == "equivocal") & (her2_fish == "negative"))
    is_tnbc = (er == "negative") & (pr == "negative") & her2_negative
    return cde_df.columns[is_tnbc]


def load_gtex_median_tpm(path=GTEX_DIR / "GTEx_Analysis_v11_gene_median_tpm.gct.gz"):
    """Load GTEx's median-TPM-by-tissue matrix (genes x tissues).

    Row index is Ensembl gene ID; a "Description" column carries the gene
    symbol. The .gct format's first two header lines (version, dimensions)
    are skipped automatically by pandas via `skiprows`.
    """
    return pd.read_csv(path, sep="\t", index_col=0, skiprows=2, compression="gzip")


def load_hpa(path=HPA_DIR / "proteinatlas.tsv"):
    """Load the Human Protein Atlas bulk TSV, indexed by gene symbol.

    One row per gene, ~119 columns covering protein class, subcellular
    location, and (among others) per-cancer-type survival-prognostic
    calls computed by HPA itself from TCGA data. HPA calls a gene
    "prognostic" only below a strict p < 0.001 threshold (log-rank test on
    Kaplan-Meier survival curves) -- deliberately conservative, since it's
    screening genome-wide. A gene reported "unprognostic" here can still
    have a real, published survival association at a more ordinary
    significance level; see NOTES.md's HPA section for a concrete example.

    11 of 20,162 gene symbols are duplicated (multiple Ensembl entries
    sharing one symbol) -- a `.loc[gene]` lookup for one of those returns
    more than one row. None of this project's current candidates hit one.
    """
    return pd.read_csv(path, sep="\t", index_col="Gene")
