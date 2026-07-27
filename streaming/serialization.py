from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd


def json_safe(value: Any) -> Any:
    if value is None or value is pd.NA:
        return None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if pd.isna(value):
        return None
    return value


def dataframe_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {str(column): json_safe(value) for column, value in row.items()}
        for row in dataframe.to_dict(orient="records")
    ]
