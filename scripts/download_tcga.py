"""Download TCGA-BRCA RNA-seq V2 (RSEM) expression and clinical data.

Source: Broad GDAC Firehose stddata__2016_01_28 run for BRCA -- the same
underlying data cBioPortal's "brca_tcga" ("TCGA, Firehose Legacy") study is
built from. Public HTTP, no account or browser needed -- unlike DepMap.

Run: python scripts/download_tcga.py
"""

import tarfile
from pathlib import Path
from urllib.request import urlretrieve

BASE = "https://gdac.broadinstitute.org/runs/stddata__2016_01_28/data/BRCA/20160128"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "tcga"

ARCHIVES = {
    "expression": (
        f"{BASE}/gdac.broadinstitute.org_BRCA.Merge_rnaseqv2__illuminahiseq_rnaseqv2"
        "__unc_edu__Level_3__RSEM_genes_normalized__data.Level_3.2016012800.0.0.tar.gz"
    ),
    "clinical": (
        f"{BASE}/gdac.broadinstitute.org_BRCA.Clinical_Pick_Tier1.Level_4.2016012800.0.0.tar.gz"
    ),
}

# Files that come out of the archives already at the top level after
# flattening; anything else (MANIFEST.txt, pipeline params) is discarded.
KEEP_RENAMED = {
    "BRCA.rnaseqv2__illuminahiseq_rnaseqv2__unc_edu__Level_3__RSEM_genes_normalized__data.data.txt": (
        "BRCA.rnaseqv2_RSEM_genes_normalized.data.txt"
    ),
}
DISCARD = {"MANIFEST.txt", "stage3_params_clin_selection_BRCA.tsv"}


def download_and_extract(url, out_dir):
    tmp_path = out_dir / Path(url).name
    urlretrieve(url, tmp_path)
    with tarfile.open(tmp_path) as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            name = Path(member.name).name  # flatten the archive's top-level folder
            if name in DISCARD:
                continue
            member.name = name
            tar.extract(member, path=out_dir, filter="data")
    tmp_path.unlink()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for label, url in ARCHIVES.items():
        print(f"Downloading {label}...")
        download_and_extract(url, OUT_DIR)
    for original, renamed in KEEP_RENAMED.items():
        (OUT_DIR / original).rename(OUT_DIR / renamed)
    print("Done.")


if __name__ == "__main__":
    main()
