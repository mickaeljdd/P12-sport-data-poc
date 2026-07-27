import time
from datetime import datetime

import pandas as pd

from database import (
    DataRepository,
    create_database_engine,
)
from etl.extract import load_hr, load_sport
from etl.load import (
    save_activities_csv,
    save_csv,
    save_pipeline_runs_csv,
    save_slack_messages_csv,
)
from etl.transform import (
    fill_missing_sports,
    merge_sources,
    normalize_transport,
)
from etl.validator import validate, validate_activities
from monitoring.logger import logger
from monitoring.pipeline_run import PipelineRun
from services.distance_service import DistanceService
from services.distance_service_factory import create_distance_service
from services.eligibility_service import EligibilityService
from services.slack_message_service import SlackMessageService
from services.wellbeing_service import WellbeingService
from simulation.activity_generator import ActivityGenerator
from simulation.live_activity_generator import LiveActivityGenerator
from streaming.config import StreamingSettings
from streaming.producer import RedpandaProducer


class Pipeline:
    def __init__(self) -> None:
        engine = create_database_engine()

        self.repository = DataRepository(engine)
        self.distance_service = DistanceService()
        self.wellbeing_service = WellbeingService()
        self.eligibility_service = EligibilityService()
        self.slack_message_service = SlackMessageService()
        self.activity_generator = ActivityGenerator()
        self.live_activity_generator = LiveActivityGenerator()
        self.streaming_settings = StreamingSettings.from_env()

        # Remplace le service par celui configuré par la factory.
        self.distance_service = create_distance_service()

    def run(
        self,
    ) -> tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
    ]:
        start_time = time.perf_counter()
        pipeline_run = PipelineRun.start()

        try:
            logger.info(
                "Démarrage du pipeline | run_id=%s",
                pipeline_run.run_id,
            )

            hr = self.extract_hr()
            sport = self.extract_sport()

            employees = self.transform(hr, sport)
            employees = self.validate(employees)
            employees = self.compute_distance(employees)
            employees = self.compute_eligibility(employees)

            is_incremental = self.repository.activities_exist()

            if is_incremental:
                new_activities = self.generate_incremental_activities(
                    employees
                )
                new_activities = validate_activities(
                    new_activities,
                    employees,
                )
                self.repository.append_activities(new_activities)
                all_activities = self.repository.read_table(
                    self.repository.ACTIVITIES_TABLE
                )
            else:
                new_activities = self.generate_activities(employees)
                new_activities = validate_activities(
                    new_activities,
                    employees,
                )
                self.repository.save_activities(new_activities)
                all_activities = new_activities

            employees = self.compute_wellbeing(
                employees,
                all_activities,
            )

            new_slack_messages = self.generate_slack_messages(
                employees,
                new_activities,
            )

            self.repository.save_employees(employees)

            if is_incremental:
                self.repository.append_slack_messages(
                    new_slack_messages
                )
            else:
                self.repository.save_slack_messages(
                    new_slack_messages
                )

            all_slack_messages = self.repository.read_table(
                self.repository.SLACK_MESSAGES_TABLE
            )

            self.export(employees)
            self.export_activities(all_activities)
            self.export_slack_messages(all_slack_messages)

            elapsed = time.perf_counter() - start_time

            pipeline_run.finished_at = datetime.now()
            pipeline_run.duration_seconds = round(elapsed, 3)
            pipeline_run.status = "SUCCESS"
            pipeline_run.employee_count = len(employees)
            pipeline_run.activity_count = len(new_activities)
            pipeline_run.slack_message_count = len(new_slack_messages)
            pipeline_run.bonus_total = float(
                employees["bonus"].sum()
            )
            pipeline_run.wellbeing_days = int(
                employees["Jours bien-être accordés"].sum()
            )

            self.repository.save_pipeline_run(
                pipeline_run.to_dataframe()
            )
            self.export_pipeline_runs()

            self.publish_streaming_events(
                activities=new_activities,
                slack_messages=new_slack_messages,
                pipeline_run=pipeline_run.to_dataframe(),
                publish_business_events=is_incremental,
            )

            logger.info(
                "Pipeline terminé avec succès en %.2f secondes "
                "| run_id=%s | mode=%s | nouvelles_activités=%s",
                elapsed,
                pipeline_run.run_id,
                "incrémental" if is_incremental else "historique",
                len(new_activities),
            )

            return (
                employees,
                all_activities,
                all_slack_messages,
            )

        except Exception as error:
            elapsed = time.perf_counter() - start_time

            pipeline_run.finished_at = datetime.now()
            pipeline_run.duration_seconds = round(elapsed, 3)
            pipeline_run.status = "FAILED"
            pipeline_run.error_message = (
                f"{type(error).__name__}: {error}"
            )

            try:
                self.repository.save_pipeline_run(
                    pipeline_run.to_dataframe()
                )
                self.export_pipeline_runs()
            except Exception:
                logger.exception(
                    "Impossible d'enregistrer ou d'exporter "
                    "l'échec du pipeline"
                )

            logger.exception(
                "Échec du pipeline | run_id=%s",
                pipeline_run.run_id,
            )
            raise

    def publish_streaming_events(
        self,
        activities: pd.DataFrame,
        slack_messages: pd.DataFrame,
        pipeline_run: pd.DataFrame,
        publish_business_events: bool,
    ) -> None:
        """Publie les événements du run lorsque Redpanda est activé.

        L'historique initial n'est pas diffusé vers Slack afin d'éviter
        plusieurs milliers de notifications. Les exécutions incrémentales
        publient une activité et un message Slack par événement.
        """
        if not self.streaming_settings.enabled:
            return

        with RedpandaProducer(self.streaming_settings) as producer:
            if publish_business_events:
                producer.publish_dataframe(
                    topic=self.streaming_settings.activities_topic,
                    dataframe=activities,
                    key_column="ID",
                    event_type="activity.created",
                )
                producer.publish_dataframe(
                    topic=self.streaming_settings.slack_topic,
                    dataframe=slack_messages,
                    key_column="ID",
                    event_type="slack.message.created",
                )

            producer.publish_dataframe(
                topic=self.streaming_settings.monitoring_topic,
                dataframe=pipeline_run,
                key_column="run_id",
                event_type="pipeline.run.completed",
            )

        logger.info(
            "Événements Redpanda publiés | activités=%s | slack=%s",
            len(activities) if publish_business_events else 0,
            len(slack_messages) if publish_business_events else 0,
        )

    def extract_hr(self) -> pd.DataFrame:
        df = load_hr()

        logger.info(
            "Données RH chargées : %s salariés",
            len(df),
        )

        return df

    def extract_sport(self) -> pd.DataFrame:
        df = load_sport()

        logger.info(
            "Données sport chargées : %s enregistrements",
            len(df),
        )

        return df

    def transform(
        self,
        hr: pd.DataFrame,
        sport: pd.DataFrame,
    ) -> pd.DataFrame:
        df = merge_sources(hr, sport)
        df = fill_missing_sports(df)
        df = normalize_transport(df)

        logger.info(
            "Transformation terminée : %s salariés",
            len(df),
        )

        return df

    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        validated_df = validate(df)

        logger.info(
            "Validation des données terminée"
        )

        return validated_df

    def compute_distance(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        enriched_df = self.distance_service.compute(df)

        logger.info(
            "Distances calculées : moyenne %.2f km, "
            "minimum %.2f km, maximum %.2f km",
            enriched_df[
                "Distance domicile-entreprise (km)"
            ].mean(),
            enriched_df[
                "Distance domicile-entreprise (km)"
            ].min(),
            enriched_df[
                "Distance domicile-entreprise (km)"
            ].max(),
        )

        return enriched_df

    def compute_eligibility(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        enriched_df = self.eligibility_service.compute(df)

        eligible_count = int(
            enriched_df["transport_eligible"].sum()
        )

        total_count = len(enriched_df)

        eligibility_rate = (
            eligible_count / total_count * 100
            if total_count > 0
            else 0
        )

        logger.info(
            "Éligibilité transport : %s salarié(s) "
            "sur %s, soit %.1f %%",
            eligible_count,
            total_count,
            eligibility_rate,
        )

        logger.info(
            "Coût total prévisionnel des primes : %.2f €",
            enriched_df["bonus"].sum(),
        )

        return enriched_df

    def generate_activities(
        self,
        employees: pd.DataFrame,
    ) -> pd.DataFrame:
        activities = self.activity_generator.generate(
            employees
        )

        invalid_activity_count = (
            activities["Type"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin({"aucun", "aucune"})
            .sum()
        )

        logger.info(
            "Activités associées à un sport invalide : %s",
            invalid_activity_count,
        )

        logger.info(
            "Activités générées sur 12 mois : %s",
            len(activities),
        )

        if not activities.empty:
            logger.info(
                "Salariés ayant au moins une activité : %s",
                activities["ID salarié"].nunique(),
            )

        logger.info(
            "Activités avec distance renseignée : %s",
            activities["Distance (m)"]
            .notna()
            .sum(),
        )

        return activities

    def generate_incremental_activities(
        self,
        employees: pd.DataFrame,
        minimum_count: int = 3,
        maximum_count: int = 10,
    ) -> pd.DataFrame:
        if minimum_count < 1 or maximum_count < minimum_count:
            raise ValueError(
                "La plage du nombre d'activités incrémentales est invalide."
            )

        activity_count = self.live_activity_generator.random.randint(
            minimum_count,
            maximum_count,
        )
        starting_id = self.repository.get_last_activity_id() + 1

        activities = self.live_activity_generator.generate(
            employees=employees,
            starting_id=starting_id,
            activity_count=activity_count,
        )

        logger.info(
            "Activités incrémentales générées : %s (IDs %s à %s)",
            len(activities),
            starting_id,
            starting_id + len(activities) - 1,
        )

        return activities

    def compute_wellbeing(
        self,
        employees: pd.DataFrame,
        activities: pd.DataFrame,
    ) -> pd.DataFrame:
        result = self.wellbeing_service.compute(
            employees,
            activities,
        )

        eligible_count = result[
            "Éligible jours bien-être"
        ].sum()

        total_days = result[
            "Jours bien-être accordés"
        ].sum()

        logger.info(
            "Salariés éligibles aux jours bien-être : %s",
            eligible_count,
        )

        logger.info(
            "Total de jours bien-être accordés : %s",
            total_days,
        )

        return result

    def generate_slack_messages(
        self,
        employees: pd.DataFrame,
        activities: pd.DataFrame,
    ) -> pd.DataFrame:
        messages = self.slack_message_service.generate(
            employees,
            activities,
        )

        logger.info(
            "Messages Slack générés : %s",
            len(messages),
        )

        return messages

    def export_slack_messages(
        self,
        messages: pd.DataFrame,
    ) -> None:
        save_slack_messages_csv(messages)

    def export_activities(
        self,
        activities: pd.DataFrame,
    ) -> None:
        save_activities_csv(activities)

        logger.info(
            "Export des activités terminé : %s lignes",
            len(activities),
        )

    def export(
        self,
        df: pd.DataFrame,
    ) -> None:
        save_csv(df)

        logger.info(
            "Export terminé : %s lignes écrites",
            len(df),
        )

    def export_pipeline_runs(self) -> None:
        """
        Exporte tout l'historique de la table pipeline_runs
        vers un CSV consommable par Power BI.
        """
        pipeline_runs = self.repository.read_table(
            self.repository.PIPELINE_RUNS_TABLE
        )

        save_pipeline_runs_csv(
            pipeline_runs,
            "data/processed/pipeline_runs.csv",
        )

        logger.info(
            "Export du monitoring terminé : %s exécution(s)",
            len(pipeline_runs),
        )
