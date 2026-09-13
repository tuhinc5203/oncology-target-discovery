"""Download the GTEx v11 median-TPM-by-tissue file.

Public GCS bucket, no account or browser needed -- unlike DepMap.

Run: python scripts/download_gtex.py
"""

from pathlib import Path
from urllib.request import urlretrieve

URL = (
    "https://storage.googleapis.com/adult-gtex/bulk-gex/v11/rna-seq/"
    "GTEx_Analysis_2025-08-22_v11_RNASeQCv2.4.3_gene_median_tpm.gct.gz"
)
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "gtex"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dest = OUT_DIR / "GTEx_Analysis_v11_gene_median_tpm.gct.gz"
    urlretrieve(URL, dest)
    print(f"Saved {dest} ({dest.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
