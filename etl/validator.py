from __future__ import annotations

import pandas as pd


EMPLOYEE_REQUIRED_COLUMNS = {
    "ID salarié",
    "Salaire brut",
    "Adresse du domicile",
    "Moyen de déplacement",
}

ACTIVITY_REQUIRED_COLUMNS = {
    "ID",
    "ID salarié",
    "Date de début de l'activité",
    "Type",
    "Distance (m)",
    "Date de fin de l'activité",
    "Commentaire",
}

ALLOWED_TRANSPORTS = {
    "Marche",
    "Vélo",
    "Trottinette",
    "Vélo/Trottinette/Autres",
    "Transports en commun",
    "Transport en commun",
    "Véhicule thermique/électrique",
    "Voiture",
}


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Valide les données RH avant le calcul des avantages."""
    _validate_required_columns(df, EMPLOYEE_REQUIRED_COLUMNS, "RH")

    errors: list[str] = []

    if df["ID salarié"].isna().any():
        errors.append("des identifiants salariés sont manquants")

    if df["ID salarié"].duplicated().any():
        errors.append("des identifiants salariés sont dupliqués")

    if df["Adresse du domicile"].isna().any() or (
        df["Adresse du domicile"].astype(str).str.strip() == ""
    ).any():
        errors.append("des adresses de domicile sont manquantes")

    salaries = pd.to_numeric(df["Salaire brut"], errors="coerce")
    if salaries.isna().any() or (salaries <= 0).any():
        errors.append("des salaires sont manquants, non numériques ou négatifs")

    transports = df["Moyen de déplacement"].astype(str).str.strip()
    invalid_transports = set(transports) - ALLOWED_TRANSPORTS
    if invalid_transports:
        values = ", ".join(sorted(invalid_transports))
        errors.append(
            f"des moyens de déplacement non reconnus : {values}"
        )

    _raise_if_errors(errors, "données RH")
    return df


def validate_activities(
    activities: pd.DataFrame,
    employees: pd.DataFrame,
) -> pd.DataFrame:
    """Valide les activités simulées avant leur chargement."""
    _validate_required_columns(
        activities,
        ACTIVITY_REQUIRED_COLUMNS,
        "activités",
    )
    _validate_required_columns(
        employees,
        {"ID salarié"},
        "salariés",
    )

    errors: list[str] = []
    start_dates = pd.to_datetime(
        activities["Date de début de l'activité"],
        errors="coerce",
    )
    end_dates = pd.to_datetime(
        activities["Date de fin de l'activité"],
        errors="coerce",
    )

    if start_dates.isna().any() or end_dates.isna().any():
        errors.append("des dates d'activité sont invalides ou manquantes")

    if (end_dates <= start_dates).any():
        errors.append(
            "des activités ont une date de fin antérieure ou égale au début"
        )

    distances = pd.to_numeric(
        activities["Distance (m)"],
        errors="coerce",
    )
    invalid_distances = (
        activities["Distance (m)"].notna() & distances.isna()
    ) | (distances < 0)
    if invalid_distances.any():
        errors.append("des distances d'activité sont invalides ou négatives")

    unknown_employees = set(activities["ID salarié"]) - set(
        employees["ID salarié"]
    )
    if unknown_employees:
        errors.append(
            "des activités sont associées à des salariés inconnus"
        )

    _raise_if_errors(errors, "données d'activité")
    return activities


def _validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    data_name: str,
) -> None:
    missing_columns = required_columns - set(dataframe.columns)
    if missing_columns:
        columns = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Colonnes manquantes dans les données {data_name} : {columns}"
        )


def _raise_if_errors(errors: list[str], data_name: str) -> None:
    if errors:
        details = "; ".join(errors)
        raise ValueError(
            f"Validation échouée pour les {data_name} : {details}."
        )
