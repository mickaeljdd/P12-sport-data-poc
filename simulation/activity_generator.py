from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

import pandas as pd


class ActivityGenerator:
    """
    Génère un historique simulé d'activités sportives.

    Le schéma produit correspond aux métadonnées demandées
    dans le cahier des charges du POC.
    """

    ACTIVITY_COLUMNS = [
        "ID",
        "ID salarié",
        "Date de début de l'activité",
        "Type",
        "Distance (m)",
        "Date de fin de l'activité",
        "Commentaire",
    ]

    WEEKLY_ACTIVITY_RANGES = {
        "occasionnel": (0, 1),
        "regulier": (1, 3),
        "intensif": (3, 5),
    }

    PROFILE_WEIGHTS = {
        "occasionnel": 0.30,
        "regulier": 0.55,
        "intensif": 0.15,
    }

    DISTANCE_CONFIG = {
        "Runing": {
            "distance_m": (3_000, 18_000),
            "speed_kmh": (7.0, 13.0),
        },
        "Randonnée": {
            "distance_m": (4_000, 25_000),
            "speed_kmh": (3.0, 6.0),
        },
        "Natation": {
            "distance_m": (500, 4_000),
            "speed_kmh": (2.0, 4.5),
        },
        "Triathlon": {
            "distance_m": (5_000, 40_000),
            "speed_kmh": (8.0, 24.0),
        },
    }

    DURATION_CONFIG = {
        "Tennis": (45, 120),
        "Badminton": (30, 90),
        "Football": (60, 110),
        "Rugby": (60, 110),
        "Basketball": (45, 100),
        "Tennis de table": (30, 90),
        "Boxe": (30, 90),
        "Judo": (45, 100),
        "Escalade": (60, 180),
        "Équitation": (45, 120),
        "Voile": (60, 240),
    }

    COMMENTS = {
        "Runing": [
            "",
            "Bonne sortie !",
            "Reprise du sport :)",
            "Très bonnes sensations.",
        ],
        "Randonnée": [
            "",
            "Très beau parcours.",
            "Une randonnée à refaire.",
            "Nouveau sentier découvert.",
        ],
        "Natation": [
            "",
            "Bonne séance.",
            "Travail d'endurance.",
        ],
        "Triathlon": [
            "",
            "Entraînement complet.",
            "Bonne préparation.",
        ],
        "default": [
            "",
            "Bonne séance.",
            "Entraînement terminé.",
            "Très bonnes sensations.",
        ],
    }

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def generate(
        self,
        employees: pd.DataFrame,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        self._validate_input(employees)

        end_date = end_date or date.today()
        start_date = start_date or end_date - timedelta(days=365)

        if start_date > end_date:
            raise ValueError(
                "La date de début doit être antérieure "
                "ou égale à la date de fin."
            )

        activities: list[dict] = []
        activity_id = 1

        for _, employee in employees.iterrows():
            if not self._practices_sport(employee):
                continue

            employee_id = employee["ID salarié"]
            sport = str(
                employee["Pratique d'un sport"]
            ).strip()

            profile = self._choose_profile()

            employee_activities = (
                self._generate_employee_activities(
                    employee_id=employee_id,
                    sport=sport,
                    profile=profile,
                    start_date=start_date,
                    end_date=end_date,
                )
            )

            for activity in employee_activities:
                activity["ID"] = activity_id
                activities.append(activity)
                activity_id += 1

        return pd.DataFrame(
            activities,
            columns=self.ACTIVITY_COLUMNS,
        )

    def _generate_employee_activities(
        self,
        employee_id: int,
        sport: str,
        profile: str,
        start_date: date,
        end_date: date,
    ) -> list[dict]:
        activities: list[dict] = []

        current_week = start_date
        minimum, maximum = self.WEEKLY_ACTIVITY_RANGES[
            profile
        ]

        while current_week <= end_date:
            count = self.random.randint(
                minimum,
                maximum,
            )

            valid_dates = [
                current_week + timedelta(days=offset)
                for offset in range(7)
                if current_week + timedelta(days=offset)
                <= end_date
            ]

            count = min(count, len(valid_dates))

            if count > 0:
                selected_dates = self.random.sample(
                    valid_dates,
                    k=count,
                )

                for activity_date in sorted(selected_dates):
                    activities.append(
                        self._build_activity(
                            employee_id=employee_id,
                            sport=sport,
                            activity_date=activity_date,
                        )
                    )

            current_week += timedelta(days=7)

        return activities

    def _build_activity(
        self,
        employee_id: int,
        sport: str,
        activity_date: date,
    ) -> dict:
        start_datetime = self._generate_start_datetime(
            activity_date
        )

        distance_m, duration_seconds = (
            self._generate_measurements(sport)
        )

        end_datetime = (
            start_datetime
            + timedelta(seconds=duration_seconds)
        )

        return {
            "ID": None,
            "ID salarié": employee_id,
            "Date de début de l'activité": start_datetime,
            "Type": sport,
            "Distance (m)": distance_m,
            "Date de fin de l'activité": end_datetime,
            "Commentaire": self._generate_comment(sport),
        }

    def _generate_measurements(
        self,
        sport: str,
    ) -> tuple[int | None, int]:
        if sport in self.DISTANCE_CONFIG:
            config = self.DISTANCE_CONFIG[sport]

            distance_m = self.random.randint(
                config["distance_m"][0],
                config["distance_m"][1],
            )

            speed_kmh = self.random.uniform(
                config["speed_kmh"][0],
                config["speed_kmh"][1],
            )

            duration_seconds = max(
                60,
                round(
                    distance_m
                    / 1000
                    / speed_kmh
                    * 3600
                ),
            )

            return distance_m, duration_seconds

        duration_range = self.DURATION_CONFIG.get(
            sport,
            (30, 90),
        )

        duration_minutes = self.random.randint(
            duration_range[0],
            duration_range[1],
        )

        return None, duration_minutes * 60

    def _generate_start_datetime(
        self,
        activity_date: date,
    ) -> datetime:
        hour = self.random.choice(
            [
                7,
                8,
                9,
                12,
                17,
                18,
                19,
            ]
        )

        minute = self.random.randint(0, 59)

        return datetime.combine(
            activity_date,
            time(hour=hour, minute=minute),
        )

    def _generate_comment(
        self,
        sport: str,
    ) -> str:
        comments = self.COMMENTS.get(
            sport,
            self.COMMENTS["default"],
        )

        return self.random.choice(comments)

    def _choose_profile(self) -> str:
        profiles = list(
            self.PROFILE_WEIGHTS.keys()
        )

        weights = list(
            self.PROFILE_WEIGHTS.values()
        )

        return self.random.choices(
            profiles,
            weights=weights,
            k=1,
        )[0]

    @staticmethod
    def _practices_sport(
        employee: pd.Series,
    ) -> bool:
        value = employee.get(
            "Pratique d'un sport"
        )

        if pd.isna(value):
            return False

        normalized_value = (
            str(value)
            .strip()
            .lower()
        )

        excluded_values = {
            "",
            "aucun",
            "aucune",
            "non",
            "néant",
        }

        return normalized_value not in excluded_values

    @staticmethod
    def _validate_input(
        employees: pd.DataFrame,
    ) -> None:
        required_columns = {
            "ID salarié",
            "Pratique d'un sport",
        }

        missing_columns = (
            required_columns
            - set(employees.columns)
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                f"Colonnes manquantes : {missing}"
            )