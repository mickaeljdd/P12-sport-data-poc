from __future__ import annotations

import pandas as pd

from config import MIN_ACTIVITIES, WELLBEING_DAYS


class WellbeingService:
    """
    Calcule l'éligibilité aux journées bien-être
    à partir des activités réalisées sur 12 mois.
    """

    def compute(
        self,
        employees: pd.DataFrame,
        activities: pd.DataFrame,
    ) -> pd.DataFrame:
        self._validate_inputs(
            employees,
            activities,
        )

        result = employees.copy()

        activity_counts = (
            activities
            .groupby("ID salarié")
            .size()
            .rename("Nombre d'activités")
        )

        result = result.merge(
            activity_counts,
            how="left",
            left_on="ID salarié",
            right_index=True,
        )

        result["Nombre d'activités"] = (
            result["Nombre d'activités"]
            .fillna(0)
            .astype(int)
        )

        result["Éligible jours bien-être"] = (
            result["Nombre d'activités"]
            >= MIN_ACTIVITIES
        )

        result["Jours bien-être accordés"] = (
            result["Éligible jours bien-être"]
            .map(
                {
                    True: WELLBEING_DAYS,
                    False: 0,
                }
            )
        )

        return result

    @staticmethod
    def _validate_inputs(
        employees: pd.DataFrame,
        activities: pd.DataFrame,
    ) -> None:
        if "ID salarié" not in employees.columns:
            raise ValueError(
                "La colonne 'ID salarié' est absente "
                "du DataFrame salariés."
            )

        if "ID salarié" not in activities.columns:
            raise ValueError(
                "La colonne 'ID salarié' est absente "
                "du DataFrame activités."
            )