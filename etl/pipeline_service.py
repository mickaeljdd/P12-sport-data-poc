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
from services.slack_webhook_service import (
    SlackWebhookService,
)
class Pipeline:
    def __init__(self) -> None:
        engine = create_database_engine()

        self.repository = DataRepository(engine)
        self.slack_webhook_service = SlackWebhookService()
        self.distance_service = DistanceService()
        self.wellbeing_service = WellbeingService()
        self.eligibility_service = EligibilityService()
        self.slack_message_service = SlackMessageService()
        self.activity_generator = ActivityGenerator()
        self.live_activity_generator = LiveActivityGenerator()
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

            incremental_mode = (
                self.repository.activities_exist()
            )

            if incremental_mode:
                new_activities = (
                    self.generate_incremental_activities(
                        employees
                    )
                )

                new_activities = validate_activities(
                    new_activities,
                    employees,
                )

                existing_activities = (
                    self.repository.read_table(
                        self.repository.ACTIVITIES_TABLE
                    )
                )

                all_activities = pd.concat(
                    [
                        existing_activities,
                        new_activities,
                    ],
                    ignore_index=True,
                )

                logger.info(
                    "Mode incrémental : %s nouvelle(s) "
                    "activité(s), %s activité(s) au total",
                    len(new_activities),
                    len(all_activities),
                )

            else:
                new_activities = self.generate_activities(
                    employees
                )

                new_activities = validate_activities(
                    new_activities,
                    employees,
                )

                all_activities = new_activities.copy()

                logger.info(
                    "Mode initial : génération de "
                    "l'historique complet"
                )

            # Le bien-être est recalculé sur tout l'historique.
            employees = self.compute_wellbeing(
                employees,
                all_activities,
            )

            # Un message Slack par nouvelle activité seulement.
            slack_messages = self.generate_slack_messages(
                employees,
                new_activities,
            )

            if incremental_mode:
                self.slack_webhook_service.send_messages(
                    slack_messages
                )
            else :
                logger.info(
                    "Mode initial : les messages Slack "
                    "ne sont pas envoyés."
                )

            self.persist_data(
                employees=employees,
                activities=new_activities,
                slack_messages=slack_messages,
                incremental_mode=incremental_mode,
            )

            # Les exports Power BI contiennent l'historique complet.
            all_activities = self.repository.read_table(
                self.repository.ACTIVITIES_TABLE
            )
            
            all_slack_messages = self.repository.read_table(
                self.repository.SLACK_MESSAGES_TABLE
            )

            self.export(employees)
            self.export_activities(all_activities)
            self.export_slack_messages(
                all_slack_messages
            )

            elapsed = time.perf_counter() - start_time

            pipeline_run.finished_at = datetime.now()
            pipeline_run.duration_seconds = round(
                elapsed,
                3,
            )
            pipeline_run.status = "SUCCESS"
            pipeline_run.employee_count = len(employees)

            # Ces compteurs représentent les données créées
            # pendant cette exécution.
            pipeline_run.activity_count = len(
                new_activities
            )
            pipeline_run.slack_message_count = len(
                slack_messages
            )

            pipeline_run.bonus_total = float(
                employees["bonus"].sum()
            )

            pipeline_run.wellbeing_days = int(
                employees[
                    "Jours bien-être accordés"
                ].sum()
            )

            self.repository.save_pipeline_run(
                pipeline_run.to_dataframe()
            )

            self.export_pipeline_runs()

            logger.info(
                "Pipeline terminé avec succès en %.2f "
                "secondes | run_id=%s",
                elapsed,
                pipeline_run.run_id,
            )

            return (
                employees,
                all_activities,
                slack_messages,
            )

        except Exception as error:
            elapsed = time.perf_counter() - start_time

            pipeline_run.finished_at = datetime.now()
            pipeline_run.duration_seconds = round(
                elapsed,
                3,
            )
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
                    "Impossible d'enregistrer ou "
                    "d'exporter l'échec du pipeline"
                )

            logger.exception(
                "Échec du pipeline | run_id=%s",
                pipeline_run.run_id,
            )

            raise

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
) -> pd.DataFrame:
        last_activity_id = (
            self.repository.get_last_activity_id()
        )

        activities = (
            self.live_activity_generator.generate(
                employees=employees,
                starting_id=last_activity_id + 1,
            )
        )

        logger.info(
            "Nouvelles activités générées : %s "
            "| IDs de %s à %s",
            len(activities),
            (
                activities["ID"].min()
                if not activities.empty
                else None
            ),
            (
                activities["ID"].max()
                if not activities.empty
                else None
            ),
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

    def persist_data(
        self,
        employees: pd.DataFrame,
        activities: pd.DataFrame,
        slack_messages: pd.DataFrame,
        incremental_mode: bool = False,
    ) -> None:
        employee_count = (
            self.repository.save_employees(
                employees
            )
        )

        if incremental_mode:
            activity_count = (
                self.repository.append_activities(
                    activities
                )
            )

            message_count = (
                self.repository.append_slack_messages(
                    slack_messages
                )
            )

            persistence_mode = "append"

        else:
            activity_count = (
                self.repository.save_activities(
                    activities
                )
            )

            message_count = (
                self.repository.save_slack_messages(
                    slack_messages
                )
            )

            persistence_mode = "replace"

        logger.info(
            "Base mise à jour en mode %s : "
            "%s salariés, "
            "%s activités, "
            "%s messages Slack",
            persistence_mode,
            employee_count,
            activity_count,
            message_count,
        )