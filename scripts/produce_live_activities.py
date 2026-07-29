from __future__ import annotations

import random
import signal
import time

import pandas as pd

from config import (
    LIVE_STREAM_MAX_INTERVAL_SECONDS,
    LIVE_STREAM_MIN_INTERVAL_SECONDS,
)
from database import (
    DataRepository,
    create_database_engine,
)
from etl.load import (
    save_activities_csv,
    save_slack_messages_csv,
)
from etl.validator import validate_activities
from monitoring.logger import logger
from services.slack_message_service import SlackMessageService
from simulation.live_activity_generator import LiveActivityGenerator
from streaming.config import StreamingSettings
from streaming.producer import RedpandaProducer


class LiveActivityProducer:
    """
    Génère et traite continuellement de nouvelles activités.

    Pour chaque activité :

    1. génération ;
    2. validation ;
    3. génération du message Slack ;
    4. ajout dans SQLite ;
    5. réexport des CSV Power BI ;
    6. publication dans Redpanda ;
    7. attente avant l'activité suivante.
    """

    def __init__(
        self,
        minimum_interval_seconds: float = 1.0,
        maximum_interval_seconds: float = 3.0,
    ) -> None:
        if minimum_interval_seconds <= 0:
            raise ValueError(
                "minimum_interval_seconds doit être "
                "strictement positif."
            )

        if maximum_interval_seconds < minimum_interval_seconds:
            raise ValueError(
                "maximum_interval_seconds doit être supérieur "
                "ou égal à minimum_interval_seconds."
            )

        self.minimum_interval_seconds = (
            minimum_interval_seconds
        )
        self.maximum_interval_seconds = (
            maximum_interval_seconds
        )

        self.random = random.Random()
        self.running = True

        engine = create_database_engine()

        self.repository = DataRepository(engine)
        self.generator = LiveActivityGenerator()
        self.slack_message_service = SlackMessageService()
        self.settings = StreamingSettings.from_env()

    def stop(
        self,
        *_: object,
    ) -> None:
        """
        Demande l'arrêt propre du producteur.
        """
        logger.info(
            "Arrêt demandé du producteur d'activités live."
        )

        self.running = False

    def load_employees(self) -> pd.DataFrame:
        """
        Charge les salariés depuis SQLite.
        """
        employees = self.repository.read_table(
            self.repository.EMPLOYEES_TABLE
        )

        if employees.empty:
            raise RuntimeError(
                "La table employees est vide. "
                "Exécutez d'abord le pipeline historique."
            )

        return employees

    def generate_activity(
        self,
        employees: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Génère et valide une nouvelle activité.
        """
        next_activity_id = (
            self.repository.get_last_activity_id() + 1
        )

        activity = self.generator.generate(
            employees=employees,
            starting_id=next_activity_id,
            activity_count=1,
        )

        if activity.empty:
            return activity

        return validate_activities(
            activity,
            employees,
        )

    def generate_slack_message(
        self,
        employees: pd.DataFrame,
        activity: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Génère le message Slack associé à l'activité.
        """
        slack_message = self.slack_message_service.generate(
            employees,
            activity,
        )

        if slack_message.empty:
            raise RuntimeError(
                "Aucun message Slack n'a été généré "
                "pour l'activité."
            )

        return slack_message

    def persist_event(
        self,
        activity: pd.DataFrame,
        slack_message: pd.DataFrame,
    ) -> None:
        """
        Ajoute l'activité et le message Slack dans SQLite.
        """
        saved_activity_count = (
            self.repository.append_activities(
                activity
            )
        )

        saved_message_count = (
            self.repository.append_slack_messages(
                slack_message
            )
        )

        logger.info(
            "Événement enregistré dans SQLite "
            "| activités=%s "
            "| messages_slack=%s",
            saved_activity_count,
            saved_message_count,
        )

    def export_power_bi_files(self) -> None:
        """
        Régénère les fichiers CSV consommés par Power BI.

        Les données sont relues depuis SQLite afin que les CSV
        représentent toujours l'état complet de la base.
        """
        all_activities = self.repository.read_table(
            self.repository.ACTIVITIES_TABLE
        )

        all_slack_messages = self.repository.read_table(
            self.repository.SLACK_MESSAGES_TABLE
        )

        save_activities_csv(
            all_activities
        )

        save_slack_messages_csv(
            all_slack_messages
        )

        logger.info(
            "Fichiers Power BI actualisés "
            "| activités=%s "
            "| messages_slack=%s",
            len(all_activities),
            len(all_slack_messages),
        )

    def publish_event(
        self,
        producer: RedpandaProducer,
        activity: pd.DataFrame,
        slack_message: pd.DataFrame,
    ) -> None:
        """
        Publie l'activité et le message Slack dans Redpanda.
        """
        published_activity_count = (
            producer.publish_dataframe(
                topic=self.settings.activities_topic,
                dataframe=activity,
                key_column="ID",
                event_type="activity.created",
            )
        )

        published_slack_count = (
            producer.publish_dataframe(
                topic=self.settings.slack_topic,
                dataframe=slack_message,
                key_column="ID",
                event_type="slack.message.created",
            )
        )

        logger.info(
            "Événement publié dans Redpanda "
            "| activités=%s "
            "| messages_slack=%s "
            "| topic_activités=%s "
            "| topic_slack=%s",
            published_activity_count,
            published_slack_count,
            self.settings.activities_topic,
            self.settings.slack_topic,
        )

    def wait_before_next_activity(self) -> None:
        """
        Attend un délai aléatoire avant la prochaine activité.
        """
        delay = self.random.uniform(
            self.minimum_interval_seconds,
            self.maximum_interval_seconds,
        )

        logger.info(
            "Prochaine activité dans %.2f seconde(s).",
            delay,
        )

        time.sleep(delay)

    def run(self) -> None:
        """
        Démarre la production continue.
        """
        if not self.settings.enabled:
            raise RuntimeError(
                "Le streaming est désactivé. "
                "Définissez STREAMING_ENABLED=true "
                "dans le fichier .env."
            )

        employees = self.load_employees()

        logger.info(
            "Producteur live démarré "
            "| prochain ID=%s "
            "| intervalle=%.1f–%.1fs "
            "| topic_activités=%s "
            "| topic_slack=%s",
            self.repository.get_last_activity_id() + 1,
            self.minimum_interval_seconds,
            self.maximum_interval_seconds,
            self.settings.activities_topic,
            self.settings.slack_topic,
        )

        with RedpandaProducer(
            self.settings
        ) as producer:
            while self.running:
                try:
                    activity = self.generate_activity(
                        employees
                    )

                    if activity.empty:
                        logger.warning(
                            "Aucune activité n'a été générée."
                        )

                        if self.running:
                            self.wait_before_next_activity()

                        continue

                    slack_message = (
                        self.generate_slack_message(
                            employees,
                            activity,
                        )
                    )

                    self.persist_event(
                        activity,
                        slack_message,
                    )

                    self.export_power_bi_files()

                    self.publish_event(
                        producer,
                        activity,
                        slack_message,
                    )

                    activity_row = activity.iloc[0]

                    logger.info(
                        "Activité live traitée avec succès "
                        "| ID=%s "
                        "| salarié=%s "
                        "| type=%s",
                        activity_row["ID"],
                        activity_row["ID salarié"],
                        activity_row["Type"],
                    )

                except Exception:
                    logger.exception(
                        "Échec du traitement d'une activité live."
                    )

                if self.running:
                    self.wait_before_next_activity()

        logger.info(
            "Producteur d'activités live arrêté."
        )


def main() -> None:
    service = LiveActivityProducer(
        minimum_interval_seconds=(
            LIVE_STREAM_MIN_INTERVAL_SECONDS
        ),
        maximum_interval_seconds=(
            LIVE_STREAM_MAX_INTERVAL_SECONDS
        ),
    )

    signal.signal(
        signal.SIGINT,
        service.stop,
    )

    if hasattr(signal, "SIGTERM"):
        signal.signal(
            signal.SIGTERM,
            service.stop,
        )

    service.run()


if __name__ == "__main__":
    main()