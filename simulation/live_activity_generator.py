from __future__ import annotations

import random
from datetime import date

import pandas as pd

from simulation.activity_generator import ActivityGenerator


class LiveActivityGenerator(ActivityGenerator):
    """
    Génère un petit nombre de nouvelles activités datées du jour.

    Cette classe ne gère volontairement ni SQLite, ni Redpanda,
    ni Slack. Elle construit uniquement les données d'activité.
    """

    def __init__(
        self,
        seed: int | None = None,
    ) -> None:
        """
        Initialise le générateur.

        Lorsque seed vaut None, les activités produites peuvent être
        différentes à chaque démarrage du programme.
        """
        super().__init__(seed=seed)

        # On conserve un générateur aléatoire dédié au mode live.
        self.random = random.Random(seed)

    def generate(
        self,
        employees: pd.DataFrame,
        starting_id: int,
        activity_count: int,
        activity_date: date | None = None,
    ) -> pd.DataFrame:
        """
        Génère un nombre précis de nouvelles activités.

        Args:
            employees:
                DataFrame contenant les salariés.

            starting_id:
                Identifiant à attribuer à la première activité.

            activity_count:
                Nombre d'activités à générer.

            activity_date:
                Date des activités. La date du jour est utilisée
                lorsqu'aucune date n'est fournie.

        Returns:
            Un DataFrame respectant les colonnes définies par
            ActivityGenerator.ACTIVITY_COLUMNS.
        """
        self._validate_input(employees)

        if starting_id < 1:
            raise ValueError(
                "starting_id doit être supérieur ou égal à 1."
            )

        if activity_count < 1:
            raise ValueError(
                "activity_count doit être supérieur ou égal à 1."
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

        rows: list[dict[str, object]] = []

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

            sport = str(
                employee["Pratique d'un sport"]
            ).strip()

            activity = self._build_activity(
                employee_id=int(
                    employee["ID salarié"]
                ),
                sport=sport,
                activity_date=generated_date,
            )

            activity["ID"] = starting_id + offset

            rows.append(activity)

        return pd.DataFrame(
            rows,
            columns=self.ACTIVITY_COLUMNS,
        )