import pandas as pd

from config import (
    SPORT_BONUS_RATE,
    WELLBEING_DAYS,
    MIN_ACTIVITIES,
    MAX_DISTANCE,
)


class EligibilityService:

    def is_transport_eligible(self,
                              employee):

        if employee.transport not in MAX_DISTANCE:
            return False

        if employee.distance_km is None:
            return False

        return (
            employee.distance_km
            <= MAX_DISTANCE[employee.transport]
        )
    
    def compute_bonus(employee):

        if employee.eligible_transport:

            return (
                employee.salary
                * SPORT_BONUS_RATE
            )

        return 0

    def compute_wellbeing_days(
            employee,
            nb_activities):

        if nb_activities >= MIN_ACTIVITIES:

            return WELLBEING_DAYS

        return 0
    
    def compute_transport(self, df: pd.DataFrame):

        df["transport_eligible"] = False

        mask = (
            df["distance_km"].notna()
        ) & (
            df["Moyen de déplacement"].isin(MAX_DISTANCE.keys())
        )

        df.loc[mask, "transport_eligible"] = (
            df.loc[mask, "distance_km"]
            <=
            df.loc[mask, "Moyen de déplacement"].map(MAX_DISTANCE)
        )

        return df
    
    def compute_bonus(self, df):

        df["bonus"] = 0

        df.loc[
            df["transport_eligible"],
            "bonus"
        ] = (
            df["Salaire brut"]
            * SPORT_BONUS_RATE
        )

        return df
    
    def compute_wellbeing_days(self, df):

        df["wellbeing_days"] = 0

        mask = (
            df["nb_activities"]
            >= MIN_ACTIVITIES
        )

        df.loc[
            mask,
            "wellbeing_days"
        ] = WELLBEING_DAYS

        return df