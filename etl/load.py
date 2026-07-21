from pathlib import Path

import pandas as pd

from monitoring.logger import logger

ROOT = Path(__file__).resolve().parent.parent

PROCESSED_PATH = ROOT / "data" / "processed"

PROCESSED_PATH.mkdir(exist_ok=True)

def save_slack_messages_csv(
    messages: pd.DataFrame,
) -> Path:
    PROCESSED_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_PATH
        / "slack_messages.csv"
    )

    messages.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    logger.info(
        "Messages Slack exportés : %s",
        output_path,
    )

    return output_path

def save_csv(df: pd.DataFrame,
             filename: str = "employees.csv") -> None:
    """
    Sauvegarde un DataFrame dans data/processed.
    """

    filepath = PROCESSED_PATH / filename

    df.to_csv(
        filepath,
        index=False,
        encoding="utf-8-sig"
    )

def save_activities_csv(df: pd.DataFrame) -> None:
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_PATH / "activities.csv"

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )
    
def save_pipeline_runs_csv(
    pipeline_runs: pd.DataFrame,
    output_path: str | Path,
) -> None:
    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pipeline_runs.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )