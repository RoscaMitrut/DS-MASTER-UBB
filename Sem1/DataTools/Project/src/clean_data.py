import pandas as pd
import numpy as np
import os

def load_and_normalize():
    # Load raw data 
    df_22 = pd.read_csv('data/raw/records_2022.csv')
    df_23 = pd.read_csv('data/raw/records_2023.csv')

    # 2023 = 'source_system', 2022 = 'source'. Normalize to 'source'.
    if 'source_system' in df_23.columns:
        df_23 = df_23.rename(columns={'source_system': 'source'})

    # 2023 = 'department'+'priority' which 2022 lacks.
    df_combined = pd.concat([df_22, df_23], ignore_index=True)

    return df_combined

def clean(df):
    # 1. Normalize strings (case/whitespace) 
    df['category'] = df['category'].str.lower().str.strip()
    df['source'] = df['source'].str.lower().str.strip()
    df['status'] = df['status'].str.lower().str.strip()
    df['priority'] = df['priority'].str.lower().str.strip()
    
    # 2. Handle missing values 
    # Fill missing text with 'Unknown' and numeric with 0
    df['category'] = df['category'].fillna('unknown')
    df['value'] = df['value'].fillna(0)
    df['unit'] = df['unit'].fillna('unknown')
    df['source'] = df['source'].fillna('unknown')
    df['status'] = df['status'].fillna('unknown')
    df['department'] = df['department'].fillna('unknown')
    df['priority'] = df['priority'].fillna('unknown')

    # 3. Deduplicate record IDs 
    df = df.drop_duplicates(subset=['record_id'], keep='last')

    # 4. Handle Outliers (Negative values) 
    df = df[df['value'] >= 0]
    
    # 5. Standardize date format
    df['date'] = pd.to_datetime(df['date'], format='mixed', dayfirst=True, errors='coerce')
    
    # 6. Add derived column: 'is_complete' if any 'unknown's or 0 value present
    df['is_complete'] = np.where(
        (df['category'] == 'unknown') |
        (df['unit'] == 'unknown') |
        (df['source'] == 'unknown') | 
        (df['status'] == 'unknown') | 
        (df['department'] == 'unknown') | 
        (df['priority'] == 'unknown') |
        (df['value'] == 0), 
        False, 
        True
    )
    
    return df

def save_data(df):
    os.makedirs('data/processed', exist_ok=True)
    
    df.to_csv('data/processed/cleaned_records.csv', index=False)
    
    df.to_parquet('data/processed/cleaned_records.parquet')
    print("Data processed and saved to data/processed/")

if __name__ == "__main__":
    df = load_and_normalize()
    df_clean = clean(df)
    save_data(df_clean)