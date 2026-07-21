from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd


DEFAULT_CACHE_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "cache"
    / "google_distances.csv"
)


class DistanceCache:
    """
    Cache persistant des distances calculées par Google Routes.

    Les adresses sont normalisées avant recherche afin de limiter
    les doublons causés par les différences de casse ou d'espacement.
    """

    ADDRESS_COLUMN = "Adresse normalisée"
    TRAVEL_MODE_COLUMN = "Mode de trajet"
    DISTANCE_COLUMN = "Distance (km)"

    def __init__(
        self,
        cache_path: Path = DEFAULT_CACHE_PATH,
    ) -> None:
        self.cache_path = cache_path

        self.cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._data = self._load()

    def get(
        self,
        address: str,
        travel_mode: str = "DRIVE",
    ) -> float | None:
        normalized_address = self.normalize_address(
            address
        )

        matching_rows = (
            self._data[self.ADDRESS_COLUMN]
            == normalized_address
        ) & (
            self._data[self.TRAVEL_MODE_COLUMN]
            == travel_mode
        )

        matches = self._data.loc[
            matching_rows,
            self.DISTANCE_COLUMN,
        ]

        if matches.empty:
            return None

        distance = matches.iloc[0]

        if pd.isna(distance):
            return None

        return float(distance)

    def set(
        self,
        address: str,
        distance_km: float,
        travel_mode: str = "DRIVE",
    ) -> None:
        normalized_address = self.normalize_address(
            address
        )

        if distance_km < 0:
            raise ValueError(
                "La distance ne peut pas être négative."
            )

        existing_mask = (
            self._data[self.ADDRESS_COLUMN]
            == normalized_address
        ) & (
            self._data[self.TRAVEL_MODE_COLUMN]
            == travel_mode
        )

        if existing_mask.any():
            self._data.loc[
                existing_mask,
                self.DISTANCE_COLUMN,
            ] = float(distance_km)
        else:
            new_row = pd.DataFrame(
                {
                    self.ADDRESS_COLUMN: [
                        normalized_address
                    ],
                    self.TRAVEL_MODE_COLUMN: [
                        travel_mode
                    ],
                    self.DISTANCE_COLUMN: [
                        float(distance_km)
                    ],
                }
            )

            if self._data.empty:
                self._data = new_row.copy()
            else:
                self._data = pd.concat(
                    [
                        self._data,
                        new_row,
                    ],
                    ignore_index=True,
                )

        self._save()

    def __len__(self) -> int:
        return len(self._data)

    def _load(self) -> pd.DataFrame:
        if not self.cache_path.exists():
            return self._empty_dataframe()

        try:
            data = pd.read_csv(
                self.cache_path,
                encoding="utf-8-sig",
            )
        except pd.errors.EmptyDataError:
            return self._empty_dataframe()

        required_columns = {
            self.ADDRESS_COLUMN,
            self.DISTANCE_COLUMN,
        }

        missing_columns = (
            required_columns
            - set(data.columns)
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "Le fichier de cache est invalide. "
                f"Colonnes manquantes : {missing}"
            )

        if self.TRAVEL_MODE_COLUMN not in data.columns:
            # Les entrées existantes ont toutes été calculées en voiture.
            data[self.TRAVEL_MODE_COLUMN] = "DRIVE"

        data = data[
            [
                self.ADDRESS_COLUMN,
                self.TRAVEL_MODE_COLUMN,
                self.DISTANCE_COLUMN,
            ]
        ].copy()

        data[self.ADDRESS_COLUMN] = (
            data[self.ADDRESS_COLUMN]
            .astype(str)
            .map(self.normalize_address)
        )

        data[self.TRAVEL_MODE_COLUMN] = (
            data[self.TRAVEL_MODE_COLUMN]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        data[self.DISTANCE_COLUMN] = (
            pd.to_numeric(
                data[self.DISTANCE_COLUMN],
                errors="coerce",
            )
        )

        data = data.drop_duplicates(
            subset=[
                self.ADDRESS_COLUMN,
                self.TRAVEL_MODE_COLUMN,
            ],
            keep="last",
        )

        return data.reset_index(
            drop=True
        )

    def _save(self) -> None:
        temporary_path = self.cache_path.with_suffix(
            ".tmp"
        )

        self._data.to_csv(
            temporary_path,
            index=False,
            encoding="utf-8-sig",
        )

        temporary_path.replace(
            self.cache_path
        )

    @classmethod
    def _empty_dataframe(
        cls,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            columns=[
                cls.ADDRESS_COLUMN,
                cls.TRAVEL_MODE_COLUMN,
                cls.DISTANCE_COLUMN,
            ]
        )

    @staticmethod
    def normalize_address(
        address: str,
    ) -> str:
        value = " ".join(
            str(address)
            .strip()
            .casefold()
            .split()
        )

        if not value:
            raise ValueError(
                "L'adresse ne peut pas être vide."
            )

        return value
