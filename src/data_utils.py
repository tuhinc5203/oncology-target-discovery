"""Loaders for this project's raw data sources.

DepMap Public 26Q1 is the only source downloaded so far. Loaders for
TCGA-BRCA and GTEx will be added once those files are in data/raw/.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEPMAP_DIR = PROJECT_ROOT / "data" / "raw" / "depmap"

DEPMAP_RELEASE = "26Q1"


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
