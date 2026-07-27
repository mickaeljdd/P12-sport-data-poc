from __future__ import annotations

import random
from datetime import date

import pandas as pd

from simulation.activity_generator import ActivityGenerator


class LiveActivityGenerator(ActivityGenerator):
    """Génère un petit lot de nouvelles activités datées du jour."""

    def __init__(self, seed: int | None = None) -> None:
        # seed=None produit une simulation différente à chaque exécution.
        self.random = random.Random(seed)

    def generate(
        self,
        employees: pd.DataFrame,
        starting_id: int,
        activity_count: int,
        activity_date: date | None = None,
    ) -> pd.DataFrame:
        self._validate_input(employees)

        if starting_id < 1:
            raise ValueError("starting_id doit être supérieur ou égal à 1.")

        if activity_count < 1:
            raise ValueError("activity_count doit être supérieur ou égal à 1.")

        sporting_employees = employees.loc[
            employees.apply(self._practices_sport, axis=1)
        ]

        if sporting_employees.empty:
            return pd.DataFrame(columns=self.ACTIVITY_COLUMNS)

        generated_date = activity_date or date.today()
        rows: list[dict] = []

        employee_indices = sporting_employees.index.tolist()

        for offset in range(activity_count):
            employee = sporting_employees.loc[
                self.random.choice(employee_indices)
            ]

            activity = self._build_activity(
                employee_id=employee["ID salarié"],
                sport=str(employee["Pratique d'un sport"]).strip(),
                activity_date=generated_date,
            )
            activity["ID"] = starting_id + offset
            rows.append(activity)

        return pd.DataFrame(rows, columns=self.ACTIVITY_COLUMNS)
