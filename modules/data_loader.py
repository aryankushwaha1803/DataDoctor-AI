
import pandas as pd
from pathlib import Path

def load_dataset(file_path):
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = file_path.suffix.lower()

    if extension == ".csv":
        encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]

        for encoding in encodings:
            try:
                return pd.read_csv(
                    file_path,
                    encoding=encoding,
                    low_memory=False
                )
            except UnicodeDecodeError:
                continue

        raise ValueError("Unable to decode this CSV file.")

    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)

    else:
        raise ValueError("Only CSV and Excel files are supported.")
