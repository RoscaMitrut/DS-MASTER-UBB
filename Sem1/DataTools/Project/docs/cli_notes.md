# PowerShell commands

## 1
```powershell
Get-Content data\raw\*.csv | Measure-Object -Line
```
Counts lines to check dataset size.

## 2
```powershell
Get-Content data\raw\records_2022.csv -TotalCount 5
```
Inspects the first 5 rows (headers).

## 3
```powershell
Select-String "2023" data\raw\records_2022.csv
```
Checks if any 2023 dates leaked into the 2022 file.

# 4
```powershell
Import-Csv data\raw\records_2022.csv | Group-Object category | Select-Object Count, Name
```
Extracts column 3 (category), sorts it, and counts unique occurrences.

# 5
```powershell
Get-Content data\raw\records_2023.csv | Set-Content data\interim\combined_raw.csv; Get-Content data\raw\records_2022.csv | Select-Object -Skip 1 | Add-Content data\interim\combined_raw.csv
```
Concatenates files for quick inspection.