import pandas as pd


def merge_sources(hr, sport):

    df = hr.merge(
        sport,
        on="ID salarié",
        how="left"
    )

    return df


def fill_missing_sports(df):

    df["Pratique d'un sport"] = (
        df["Pratique d'un sport"]
        .fillna("Aucune")
    )

    return df


def normalize_transport(df):

    mapping = {
        "Marche/running": "Marche",
        "Running": "Marche",
        "Course à pied": "Marche",
        "A pied": "Marche",

        "Vélo": "Vélo",
        "Trottinette": "Trottinette",

        "Voiture": "Voiture",
        "Transport en commun": "Transport en commun",
        "Transports en commun": "Transports en commun",
        "véhicule thermique/électrique": "Véhicule thermique/électrique",
        "Véhicule thermique/électrique": "Véhicule thermique/électrique",
    }

    df["Moyen de déplacement"] = (
        df["Moyen de déplacement"]
        .replace(mapping)
        .str.strip()
    )

    return df
