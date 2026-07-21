from __future__ import annotations

import random
from datetime import date

import pandas as pd

from config import (
    MAX_INCREMENTAL_ACTIVITIES,
    MIN_INCREMENTAL_ACTIVITIES,
)
from simulation.activity_generator import ActivityGenerator


class LiveActivityGenerator(ActivityGenerator):
    """Génère un petit lot de nouvelles activités."""

    def __init__(
        self,
        seed: int | None = None,
    ) -> None:
        self.random = random.Random(seed)

    def generate(
        self,
        employees: pd.DataFrame,
        starting_id: int,
        activity_date: date | None = None,
    ) -> pd.DataFrame:
        """
        Génère un nombre aléatoire de nouvelles activités.

        Le nombre généré est compris entre
        MIN_INCREMENTAL_ACTIVITIES et
        MAX_INCREMENTAL_ACTIVITIES.
        """
        self._validate_input(employees)

        if starting_id < 1:
            raise ValueError(
                "starting_id doit être supérieur "
                "ou égal à 1."
            )

        if MIN_INCREMENTAL_ACTIVITIES < 1:
            raise ValueError(
                "MIN_INCREMENTAL_ACTIVITIES doit être "
                "supérieur ou égal à 1."
            )

        if (
            MAX_INCREMENTAL_ACTIVITIES
            < MIN_INCREMENTAL_ACTIVITIES
        ):
            raise ValueError(
                "MAX_INCREMENTAL_ACTIVITIES doit être "
                "supérieur ou égal à "
                "MIN_INCREMENTAL_ACTIVITIES."
            )

        activity_count = self.random.randint(
            MIN_INCREMENTAL_ACTIVITIES,
            MAX_INCREMENTAL_ACTIVITIES,
        )

        sporting_employees = employees.loc[
            employees.apply(
                self._practices_sport,
                axis=1,
            )
        ]

        if sporting_employees.empty:
            return pd.DataFrame(
                columns=self.ACTIVITY_COLUMNS
            )

        generated_date = activity_date or date.today()

        rows: list[dict] = []

        employee_indices = (
            sporting_employees.index.tolist()
        )

        for offset in range(activity_count):
            employee_index = self.random.choice(
                employee_indices
            )

            employee = sporting_employees.loc[
                employee_index
            ]

            activity = self._build_activity(
                employee_id=int(
                    employee["ID salarié"]
                ),
                sport=str(
                    employee[
                        "Pratique d'un sport"
                    ]
                ).strip(),
                activity_date=generated_date,
            )

            activity["ID"] = starting_id + offset

            rows.append(activity)

        return pd.DataFrame(
            rows,
            columns=self.ACTIVITY_COLUMNS,
        )