# Data Toolkit Final Project
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Educational-green.svg)

## Overview
This repository contains a reproducible workflow for the Synthetic Institutional Records Dataset. It ingests raw CSVs, handles schema drift between 2022/2023, and produces cleaned data and reports.

## Structure
- `data/`: Raw (immutable) and Processed data.
- `src/`: Python processing scripts.
- `docs/`: Data dictionaries and integrity checks.
- `Snakefile`: Entry point for the pipeline.

## Reproducibility Instructions

### Initial system requirements
- Windows
- Python
- Pip
- Snakemake (pip install snakemake)
Any other dependencies are resolved when using the provided command

### Reproducing the project
To reproduce the entire project (environment setup + data processing + reporting) from a fresh clone, make sure the 2 data files are placed inside `data/raw`, then run this single command:

```bash
python -m snakemake -c1
```

### Cleaning up
To clean up the project to a fresh start, run this single command:

```bash
python -m snakemake -c1 clean
```
## Data Notes
The raw data contained negative values (removed), missing values(filled with either 'unknown' or 0) and inconsistent column names (`source` vs `source_system`), which are resolved in the cleaning step.

## Citation and Reuse
How to Cite: Please cite this repository internally as:

Synthetic Institutional Records Dataset v1.0, Data Toolkit Course, 2026.