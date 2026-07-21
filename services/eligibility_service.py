import pandas as pd

from config import MAX_DISTANCE, SPORT_BONUS_RATE


class EligibilityService:
    """
    Détermine l'éligibilité des salariés
    aux avantages sportifs.
    """

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:

        df = df.copy()

        # Distance maximale autorisée selon le transport
        df["distance_limit"] = (
            df["Moyen de déplacement"]
            .map(MAX_DISTANCE)
        )

        # Employés éligibles
        df["transport_eligible"] = (
            df["Distance domicile-entreprise (km)"]
            <= df["distance_limit"]
        )

        # Les transports non concernés (voiture, etc.)
        df["transport_eligible"] = (
            df["transport_eligible"]
            .fillna(False)
        )

        # Calcul de la prime
        df["bonus"] = 0.0

        df.loc[
            df["transport_eligible"],
            "bonus"
        ] = (
            df["Salaire brut"]
            * SPORT_BONUS_RATE
        )

        return df