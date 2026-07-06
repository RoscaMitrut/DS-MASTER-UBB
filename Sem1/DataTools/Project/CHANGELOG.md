# Changelog

## [1.0.0] - 2026-01-04
### Added
- Initial project structure and .gitignore.
- Python cleaning script handling schema drift.
- Snakemake for automated reproducibility.
- Documentation (Metadata, Data Dictionary).
- Documentation suite.
- CLI notes for Windows (PowerShell).
- Derived 'is_complete' column logic to flag records containing missing values or zero values.
- Parquet export support in addition to CSV.

### Fixed
- Removed negative values from raw data.
- Deduplicated records based on 'record_id', keeping the most recent entry.

 ### Changed
- Normalized 'source_system' column in 2023 data to match 2022 'source'.
- Normalized string columns (category, source, status, priority): converted to lowercase, stripped whitespace.
- Filled missing text entries (category, unit, source, status, department, priority) with 'unknown'.
- Filled missing 'value' entries with 0.
- Standardized date column to datetime objects, handling mixed formats.