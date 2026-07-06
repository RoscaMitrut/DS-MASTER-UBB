# Formats Notes

I chose Apache Parquet as the secondary format because it is a binary, columnar storage format that offers significant compression and faster read speeds compared to row-based CSVs. Unlike CSV, Parquet preserves specific data types (e.g., distinguishing floats from strings), which prevents type inference errors during downstream analysis. 

Regarding schema evolution, the final output merges the disjoint schemas of 2022 and 2023. The 'source' and 'source_system' columns were merged into a single 'source' field, and new columns from 2023 ('department', 'priority') were filled with 'unknown' for 2022 records.