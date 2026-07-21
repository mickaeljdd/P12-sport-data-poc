from __future__ import annotations

import pandas as pd


class SlackMessageService:
    """
    Génère des messages Slack à partir des activités sportives.

    Ce service ne réalise aucun appel réseau. Il prépare uniquement
    les messages qui pourront ensuite être envoyés vers Slack.
    """

    REQUIRED_EMPLOYEE_COLUMNS = {
        "ID salarié",
        "Prénom",
        "Nom",
    }

    REQUIRED_ACTIVITY_COLUMNS = {
        "ID",
        "ID salarié",
        "Date de début de l'activité",
        "Date de fin de l'activité",
        "Type",
        "Distance (m)",
        "Commentaire",
    }

    def generate(
        self,
        employees: pd.DataFrame,
        activities: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Génère un message Slack pour chaque activité.

        Retourne un DataFrame distinct pour ne pas modifier les
        données sources.
        """

        self._validate_inputs(
            employees,
            activities,
        )

        employees_identity = employees[
            [
                "ID salarié",
                "Prénom",
                "Nom",
            ]
        ].copy()

        result = activities.merge(
            employees_identity,
            on="ID salarié",
            how="left",
            validate="many_to_one",
        )

        missing_employee = (
            result["Prénom"].isna()
            | result["Nom"].isna()
        )

        if missing_employee.any():
            employee_ids = (
                result.loc[
                    missing_employee,
                    "ID salarié",
                ]
                .drop_duplicates()
                .tolist()
            )

            raise ValueError(
                "Certaines activités ne correspondent à aucun "
                f"salarié : {employee_ids}"
            )

        result["Durée (min)"] = (
            (
                result["Date de fin de l'activité"]
                - result["Date de début de l'activité"]
            )
            .dt.total_seconds()
            .div(60)
            .round()
            .astype(int)
        )

        result["Message Slack"] = result.apply(
            self._build_message,
            axis=1,
        )

        return result[
            [
                "ID",
                "ID salarié",
                "Date de début de l'activité",
                "Message Slack",
            ]
        ].copy()

    def _build_message(
        self,
        activity: pd.Series,
    ) -> str:
        first_name = str(
            activity["Prénom"]
        ).strip()

        last_name = str(
            activity["Nom"]
        ).strip()

        sport = str(
            activity["Type"]
        ).strip()

        duration = int(
            activity["Durée (min)"]
        )

        distance = activity["Distance (m)"]
        comment = activity["Commentaire"]

        introduction = self._build_introduction(
            first_name=first_name,
            last_name=last_name,
            sport=sport,
            distance=distance,
            duration=duration,
        )

        formatted_comment = self._format_comment(
            comment
        )

        if formatted_comment:
            return (
                f"{introduction} "
                f'("{formatted_comment}")'
            )

        return introduction

    def _build_introduction(
        self,
        first_name: str,
        last_name: str,
        sport: str,
        distance: object,
        duration: int,
    ) -> str:
        full_name = f"{first_name} {last_name}"

        sport_normalized = sport.casefold()

        if sport_normalized in {
            "runing",
            "running",
            "course",
            "course à pied",
        }:
            if self._has_distance(distance):
                distance_km = self._format_distance(
                    distance
                )

                return (
                    f"Bravo {full_name} ! "
                    f"Tu viens de courir {distance_km} km "
                    f"en {duration} min ! "
                    "Quelle énergie ! 🔥🏅"
                )

            return (
                f"Bravo {full_name} ! "
                f"Tu viens de terminer une course "
                f"de {duration} min ! 🔥🏅"
            )

        if sport_normalized == "randonnée":
            if self._has_distance(distance):
                distance_km = self._format_distance(
                    distance
                )

                return (
                    f"Magnifique {full_name} ! "
                    f"Une randonnée de {distance_km} km "
                    "terminée et un nouveau spot "
                    "à découvrir ! 🌄"
                )

            return (
                f"Magnifique {full_name} ! "
                f"Une randonnée de {duration} min "
                "terminée ! 🌄"
            )

        if self._has_distance(distance):
            distance_km = self._format_distance(
                distance
            )

            return (
                f"Bravo {full_name} ! "
                f"Tu viens de terminer une activité "
                f"de {sport} de {distance_km} km "
                f"en {duration} min ! 💪"
            )

        return (
            f"Bravo {full_name} ! "
            f"Tu viens de terminer une activité "
            f"de {sport} de {duration} min ! 💪"
        )

    @staticmethod
    def _has_distance(
        distance: object,
    ) -> bool:
        if pd.isna(distance):
            return False

        return float(distance) > 0

    @staticmethod
    def _format_distance(
        distance_m: object,
    ) -> str:
        distance_km = float(distance_m) / 1000

        formatted = f"{distance_km:.1f}"

        return formatted.replace(".", ",")

    @staticmethod
    def _format_comment(
        comment: object,
    ) -> str:
        if pd.isna(comment):
            return ""

        return str(comment).strip()

    def _validate_inputs(
        self,
        employees: pd.DataFrame,
        activities: pd.DataFrame,
    ) -> None:
        missing_employee_columns = (
            self.REQUIRED_EMPLOYEE_COLUMNS
            - set(employees.columns)
        )

        if missing_employee_columns:
            missing = ", ".join(
                sorted(missing_employee_columns)
            )

            raise ValueError(
                "Colonnes salariés manquantes : "
                f"{missing}"
            )

        missing_activity_columns = (
            self.REQUIRED_ACTIVITY_COLUMNS
            - set(activities.columns)
        )

        if missing_activity_columns:
            missing = ", ".join(
                sorted(missing_activity_columns)
            )

            raise ValueError(
                "Colonnes activités manquantes : "
                f"{missing}"
            )

        if not pd.api.types.is_datetime64_any_dtype(
            activities[
                "Date de début de l'activité"
            ]
        ):
            raise ValueError(
                "La date de début doit être au format datetime."
            )

        if not pd.api.types.is_datetime64_any_dtype(
            activities[
                "Date de fin de l'activité"
            ]
        ):
            raise ValueError(
                "La date de fin doit être au format datetime."
            )

        invalid_dates = (
            activities[
                "Date de fin de l'activité"
            ]
            <= activities[
                "Date de début de l'activité"
            ]
        )

        if invalid_dates.any():
            raise ValueError(
                "Une activité contient une date de fin "
                "antérieure ou égale à sa date de début."
            )