import pandas as pd


def check_duplicate_employee(df):

    duplicates = df[df.duplicated(subset="ID salarié", keep=False)]

    if not duplicates.empty:
        print("Doublons détectés :")
        print(duplicates)

    return duplicates


def check_missing_addresses(df):

    missing = df[
    df["Adresse du domicile"].isna()
    |
    (df["Adresse du domicile"].str.strip() == "")
]

    if not missing.empty:
        print("Adresses manquantes :")
        print(missing)

    return missing


def check_negative_salary(df):

    errors = df[df["Salaire brut"] <= 0]

    if not errors.empty:
        print("Salaires invalides :")
        print(errors)

    return errors

def validate(df):
    """
    Lance l'ensemble des contrôles de qualité.
    """

    print("\n===== VALIDATION =====")

    duplicates = check_duplicate_employee(df)
    missing = check_missing_addresses(df)
    salary_errors = check_negative_salary(df)

    print(f"Doublons : {len(duplicates)}")
    print(f"Adresses manquantes : {len(missing)}")
    print(f"Salaires invalides : {len(salary_errors)}")

    print("Validation terminée.\n")

    return df