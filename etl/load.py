from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

OUTPUT = ROOT / "data" / "processed"

OUTPUT.mkdir(exist_ok=True)


def save_csv(df: pd.DataFrame,
             filename: str = "employees.csv") -> None:
    """
    Sauvegarde un DataFrame dans data/processed.
    """

    filepath = OUTPUT / filename

    df.to_csv(
        filepath,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nFichier créé : {filepath}")