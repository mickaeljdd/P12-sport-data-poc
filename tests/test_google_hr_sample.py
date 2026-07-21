from __future__ import annotations

from etl.extract import load_hr
from services.google_maps_distance_service import (
    GoogleMapsDistanceService,
)


def main() -> None:
    employees = load_hr()

    sample = employees.head(2).copy()

    service = GoogleMapsDistanceService()

    result = service.compute(sample)

    columns_to_display = [
        "ID salarié",
        "Distance domicile-entreprise (km)",
    ]

    print(
        result[columns_to_display].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()