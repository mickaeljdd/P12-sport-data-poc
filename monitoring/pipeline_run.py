from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

import pandas as pd


@dataclass
class PipelineRun:
    run_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: str = "RUNNING"
    employee_count: int = 0
    activity_count: int = 0
    slack_message_count: int = 0
    bonus_total: float = 0.0
    wellbeing_days: int = 0
    error_message: Optional[str] = None

    @classmethod
    def start(cls) -> "PipelineRun":
        return cls(
            run_id=str(uuid4()),
            started_at=datetime.now(),
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(self)])