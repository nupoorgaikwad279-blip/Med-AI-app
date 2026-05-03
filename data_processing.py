import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import numpy as np

def clean_data(df):
    """
    Dynamically clean the incoming dataframe.
    - Handle missing values (mean for numerical, mode for categorical)
    - Remove duplicates
    - Encode categorical values
    - Normalize numerical values
    """
    if df is None or df.empty:
        return df

    # 1. Remove duplicates
    df = df.drop_duplicates()

    # Separate numerical and categorical columns dynamically
    num_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.select_dtypes(exclude=[np.number]).columns

    # 2. Handle Missing Values
    for col in num_cols:
        df[col] = df[col].fillna(df[col].mean())
    for col in cat_cols:
        # Fill with mode if mode exists, else "Unknown"
        mode_val = df[col].mode()
        fill_val = mode_val[0] if not mode_val.empty else "Unknown"
        df[col] = df[col].fillna(fill_val)

    # 3. Label Encode Categorical Columns
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        # Convert to string to avoid mixed types during encoding
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    # 4. Normalize Numerical Columns
    # Skip normalization for obvious ID columns or Target columns if detected
    skip_norm = [c for c in num_cols if c.lower() in ["id", "patient_id", "target", "outcome", "readmission"]]
    norm_cols = [c for c in num_cols if c not in skip_norm]
    
    if norm_cols:
        scaler = MinMaxScaler()
        df[norm_cols] = scaler.fit_transform(df[norm_cols])

    return df

def get_stats(df_before, df_after):
    if df_before is None or df_after is None:
        return {}
    
    return {
        "rows_before": len(df_before),
        "rows_after": len(df_after),
        "duplicates_removed": len(df_before) - len(df_before.drop_duplicates()),
        "missing_handled": int(df_before.isnull().sum().sum()),
        "columns": list(df_after.columns)
    }
