from __future__ import annotations

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


class DataRepository:
    """
    Centralise l'écriture et la lecture des données du POC.
    """

    EMPLOYEES_TABLE = "employees"
    ACTIVITIES_TABLE = "activities"
    SLACK_MESSAGES_TABLE = "slack_messages"
    PIPELINE_RUNS_TABLE = "pipeline_runs"

    ACTIVITY_REQUIRED_COLUMNS = {
        "ID",
        "ID salarié",
        "Date de début de l'activité",
        "Type",
        "Distance (m)",
        "Date de fin de l'activité",
        "Commentaire",
    }

    SLACK_MESSAGE_REQUIRED_COLUMNS = {
        "ID",
        "ID salarié",
        "Message Slack",
    }

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        self.engine = engine

    def save_employees(
        self,
        employees: pd.DataFrame,
    ) -> int:
        self._validate_dataframe(
            employees,
            required_columns={"ID salarié"},
            dataframe_name="salariés",
        )

        employees.to_sql(
            self.EMPLOYEES_TABLE,
            con=self.engine,
            if_exists="replace",
            index=False,
        )

        return len(employees)

    def save_activities(
        self,
        activities: pd.DataFrame,
    ) -> int:
        """
        Remplace l'historique complet des activités.
        """
        self._validate_dataframe(
            activities,
            required_columns=self.ACTIVITY_REQUIRED_COLUMNS,
            dataframe_name="activités",
        )

        activities.to_sql(
            self.ACTIVITIES_TABLE,
            con=self.engine,
            if_exists="replace",
            index=False,
        )

        return len(activities)

    def append_activities(
        self,
        activities: pd.DataFrame,
    ) -> int:
        """
        Ajoute uniquement de nouvelles activités à l'historique.
        """
        self._validate_dataframe(
            activities,
            required_columns=self.ACTIVITY_REQUIRED_COLUMNS,
            dataframe_name="activités",
        )

        if activities.empty:
            return 0

        activities.to_sql(
            self.ACTIVITIES_TABLE,
            con=self.engine,
            if_exists="append",
            index=False,
        )

        return len(activities)

    def activities_exist(self) -> bool:
        """
        Indique si la table activities existe et contient
        au moins une ligne.
        """
        table_exists = inspect(
            self.engine
        ).has_table(
            self.ACTIVITIES_TABLE
        )

        if not table_exists:
            return False

        query = text(
            f'SELECT 1 '
            f'FROM "{self.ACTIVITIES_TABLE}" '
            f'LIMIT 1'
        )

        with self.engine.connect() as connection:
            result = connection.execute(
                query
            ).first()

        return result is not None

    def get_last_activity_id(self) -> int:
        """
        Retourne le plus grand identifiant d'activité.

        Retourne 0 si la table n'existe pas ou ne contient
        aucune activité.
        """
        table_exists = inspect(
            self.engine
        ).has_table(
            self.ACTIVITIES_TABLE
        )

        if not table_exists:
            return 0

        query = text(
            f'SELECT MAX("ID") '
            f'FROM "{self.ACTIVITIES_TABLE}"'
        )

        with self.engine.connect() as connection:
            last_activity_id = connection.execute(
                query
            ).scalar_one_or_none()

        if last_activity_id is None:
            return 0

        return int(last_activity_id)

    def save_slack_messages(
        self,
        messages: pd.DataFrame,
    ) -> int:
        """
        Remplace l'historique complet des messages Slack.
        """
        self._validate_dataframe(
            messages,
            required_columns=self.SLACK_MESSAGE_REQUIRED_COLUMNS,
            dataframe_name="messages Slack",
        )

        messages.to_sql(
            self.SLACK_MESSAGES_TABLE,
            con=self.engine,
            if_exists="replace",
            index=False,
        )

        return len(messages)

    def append_slack_messages(
        self,
        messages: pd.DataFrame,
    ) -> int:
        """
        Ajoute uniquement les messages correspondant
        aux nouvelles activités.
        """
        self._validate_dataframe(
            messages,
            required_columns=self.SLACK_MESSAGE_REQUIRED_COLUMNS,
            dataframe_name="messages Slack",
        )

        if messages.empty:
            return 0

        messages.to_sql(
            self.SLACK_MESSAGES_TABLE,
            con=self.engine,
            if_exists="append",
            index=False,
        )

        return len(messages)

    def save_pipeline_run(
        self,
        pipeline_run: pd.DataFrame,
    ) -> int:
        self._validate_dataframe(
            pipeline_run,
            required_columns={
                "run_id",
                "started_at",
                "finished_at",
                "duration_seconds",
                "status",
                "employee_count",
                "activity_count",
                "slack_message_count",
                "bonus_total",
                "wellbeing_days",
                "error_message",
            },
            dataframe_name="exécutions du pipeline",
        )

        pipeline_run.to_sql(
            self.PIPELINE_RUNS_TABLE,
            con=self.engine,
            if_exists="append",
            index=False,
        )

        return len(pipeline_run)

    def read_table(
        self,
        table_name: str,
    ) -> pd.DataFrame:
        allowed_tables = {
            self.EMPLOYEES_TABLE,
            self.ACTIVITIES_TABLE,
            self.SLACK_MESSAGES_TABLE,
            self.PIPELINE_RUNS_TABLE,
        }

        if table_name not in allowed_tables:
            raise ValueError(
                f"Table non autorisée : {table_name}"
            )

        return pd.read_sql_table(
            table_name,
            con=self.engine,
        )

    @staticmethod
    def _validate_dataframe(
        dataframe: pd.DataFrame,
        required_columns: set[str],
        dataframe_name: str,
    ) -> None:
        missing_columns = (
            required_columns
            - set(dataframe.columns)
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                f"Colonnes manquantes dans les "
                f"données {dataframe_name} : {missing}"
            )