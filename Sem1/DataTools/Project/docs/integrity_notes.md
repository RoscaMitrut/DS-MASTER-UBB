# Data Integrity Verification

## Overview
To ensure the raw dataset has not suffered from accidental corruption, bit rot, or unauthorized modification, we verify file integrity using SHA-256 checksums.

The checksums are stored in `docs/checksums.sha256`.

## How to Verify
We use a Python script to perform the verification.

### Option 1: Manual Verification (Command Line)
To verify the raw data manually, run the following command from the project root:
```bash
python src/checksum.py verify
```

Expected output: If the files are intact, you will see:
```
OK: data/raw/records_2022.csv
OK: data/raw/records_2023.csv
```

### Option 2: Automated Verification (Snakemake)
The automated pipeline includes integrity verification as the first step. When you run the workflow, it automatically checks hashes before processing any data.
If verification fails, the pipeline will stop immediately to prevent processing corrupted data.
