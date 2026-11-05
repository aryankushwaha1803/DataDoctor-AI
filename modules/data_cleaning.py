
import pandas as pd

def clean_data(df, fill_missing=True, remove_duplicates=False, trim_text=True):
    cleaned = df.copy(deep=True)
    changes = []

    if fill_missing:
        for col in cleaned.columns:
            if cleaned[col].isnull().any():
                if pd.api.types.is_numeric_dtype(cleaned[col]):
                    cleaned[col] = cleaned[col].fillna(cleaned[col].mean())
                else:
                    mode = cleaned[col].mode()
                    if not mode.empty:
                        cleaned[col] = cleaned[col].fillna(mode.iloc[0])
                changes.append(f"Handled missing values in {col}")

    if trim_text:
        for col in cleaned.select_dtypes(include="object").columns:
            cleaned[col] = cleaned[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )

    if remove_duplicates:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        removed = before - len(cleaned)
        if removed:
            changes.append(f"Removed {removed} duplicate rows")

    summary = {
        "original_rows": len(df),
        "cleaned_rows": len(cleaned),
        "original_missing": int(df.isnull().sum().sum()),
        "cleaned_missing": int(cleaned.isnull().sum().sum()),
        "changes": changes
    }

    return cleaned, summary
