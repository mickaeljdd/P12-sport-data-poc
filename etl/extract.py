from pathlib import Path
import pandas as pd
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "raw"
def load_hr():
    df = pd.read_excel(DATA_PATH / "Donnees+RH.xlsx")

    expected_columns = [
        "ID salarié",
        "Nom",
        "Prénom",
        "Date de naissance",
        "BU",
        "Date d'embauche",
        "Salaire brut",
        "Type de contrat",
        "Nombre de jours de CP",
        "Adresse du domicile",
        "Moyen de déplacement",
    ]

    missing = set(expected_columns) - set(df.columns)

    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")
    return df


def load_sport():
    df = pd.read_excel(DATA_PATH / "Donnees+Sportive.xlsx")

    expected_columns = [
        "ID salarié",
        "Pratique d'un sport",
    ]

    missing = set(expected_columns) - set(df.columns)

    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    return df