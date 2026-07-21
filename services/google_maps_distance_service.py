from __future__ import annotations
from services.distance_cache import DistanceCache
import time
from typing import Any
from monitoring.logger import logger
import pandas as pd
import requests

from config import (
    COMPANY_ADDRESS,
    GOOGLE_MAPS_API_KEY,
    GOOGLE_MAPS_TIMEOUT_SECONDS,
    GOOGLE_ROUTES_URL,
)
from services.exceptions import DistanceServiceError


class GoogleMapsDistanceService:
    """
    Calcule la distance routière entre le domicile
    d'un salarié et l'entreprise via Google Routes API.
    """
    ADDRESS_COLUMN = "Adresse du domicile"
    TRANSPORT_COLUMN = "Moyen de déplacement"

    TRAVEL_MODE_BY_TRANSPORT = {
        "Marche": "WALK",
        "Vélo": "BICYCLE",
        "Trottinette": "BICYCLE",
        "Vélo/Trottinette/Autres": "BICYCLE",
        "Transports en commun": "TRANSIT",
        "Transport en commun": "TRANSIT",
        "Véhicule thermique/électrique": "DRIVE",
        "Voiture": "DRIVE",
    }

    REQUIRED_COLUMNS = {
        ADDRESS_COLUMN,
        TRANSPORT_COLUMN,
    }

    def __init__(
    self,
    api_key: str | None = GOOGLE_MAPS_API_KEY,
    company_address: str = COMPANY_ADDRESS,
    timeout_seconds: int = GOOGLE_MAPS_TIMEOUT_SECONDS,
    max_retries: int = 3,
    cache: DistanceCache | None = None,
) -> None:
        if not api_key:
            raise ValueError(
                "La variable GOOGLE_MAPS_API_KEY "
                "n'est pas configurée."
            )

        if not company_address.strip():
            raise ValueError(
                "L'adresse de l'entreprise est vide."
            )

        self.api_key = api_key
        self.company_address = (
            company_address.strip()
        )
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        self.session = requests.Session()

        self.cache = (
            cache
            if cache is not None
            else DistanceCache()
        )

    def compute(
    self,
    employees: pd.DataFrame,
) -> pd.DataFrame:
        self._validate_input(employees)

        result = employees.copy()

        distances: list[float | None] = []

        cache_hits = 0
        google_calls = 0
        missing_addresses = 0

        for _, employee in result.iterrows():
            address = employee[self.ADDRESS_COLUMN]
            travel_mode = self._get_travel_mode(
                employee[self.TRANSPORT_COLUMN]
            )
            normalized_address = (
                self._normalize_address(address)
            )

            if normalized_address is None:
                distances.append(None)
                missing_addresses += 1
                continue

            cached_distance = self.cache.get(
                normalized_address,
                travel_mode,
            )

            if cached_distance is not None:
                distances.append(
                    cached_distance
                )
                cache_hits += 1
                continue

            distance_km = self.get_distance_km(
                normalized_address,
                travel_mode,
            )

            self.cache.set(
                normalized_address,
                distance_km,
                travel_mode,
            )

            distances.append(
                distance_km
            )

            google_calls += 1

        result[
            "Distance domicile-entreprise (km)"
        ] = distances

        logger.info(
            (
                "Calcul des distances terminé : "
                "%s valeur(s) depuis le cache, "
                "%s appel(s) Google, "
                "%s adresse(s) manquante(s)."
            ),
            cache_hits,
            google_calls,
            missing_addresses,
        )

        return result

    def get_distance_km(
        self,
        origin_address: str,
        travel_mode: str,
    ) -> float:
        payload = {
            "origin": {
                "address": origin_address,
            },
            "destination": {
                "address": self.company_address,
            },
            "travelMode": travel_mode,
            "languageCode": "fr-FR",
            "units": "METRIC",
        }

        if travel_mode == "DRIVE":
            payload["routingPreference"] = (
                "TRAFFIC_UNAWARE"
            )

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "routes.distanceMeters,"
                "routes.duration"
            ),
        }

        for attempt in range(
            1,
            self.max_retries + 1,
        ):
            try:
                response = self.session.post(
                    GOOGLE_ROUTES_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    self._retry_or_raise(
                        attempt=attempt,
                        message=(
                            "Erreur temporaire Google Routes : "
                            f"HTTP {response.status_code}"
                        ),
                    )
                    continue

                response.raise_for_status()

                return self._extract_distance_km(
                    response.json()
                )

            except requests.Timeout as exc:
                self._retry_or_raise(
                    attempt=attempt,
                    message=(
                        "Délai dépassé lors de l'appel "
                        "à Google Routes."
                    ),
                    cause=exc,
                )

            except requests.RequestException as exc:
                print("===== ERREUR GOOGLE =====")
                if hasattr(exc, "response") and exc.response is not None:
                    print("Status :", exc.response.status_code)
                    print("Réponse :", exc.response.text)
                else:
                    print(exc)

                raise

        raise DistanceServiceError(
            "Impossible de calculer la distance."
        )

    def _extract_distance_km(
        self,
        payload: dict[str, Any],
    ) -> float:
        routes = payload.get("routes", [])

        if not routes:
            raise DistanceServiceError(
                "Google Routes n'a retourné "
                "aucun itinéraire."
            )

        distance_meters = routes[0].get(
            "distanceMeters"
        )

        if distance_meters is None:
            raise DistanceServiceError(
                "La réponse Google ne contient "
                "pas de distance."
            )

        return round(
            float(distance_meters) / 1000,
            2,
        )

    def _retry_or_raise(
        self,
        attempt: int,
        message: str,
        cause: Exception | None = None,
    ) -> None:
        if attempt >= self.max_retries:
            raise DistanceServiceError(
                message
            ) from cause

        time.sleep(2 ** (attempt - 1))

    @staticmethod
    def _normalize_address(
        address: object,
    ) -> str | None:
        if pd.isna(address):
            return None

        value = " ".join(
            str(address)
            .strip()
            .split()
        )

        return value or None

    @classmethod
    def _get_travel_mode(
        cls,
        transport: object,
    ) -> str:
        normalized_transport = str(transport).strip()

        try:
            return cls.TRAVEL_MODE_BY_TRANSPORT[
                normalized_transport
            ]
        except KeyError as exc:
            raise ValueError(
                "Moyen de déplacement non reconnu : "
                f"{normalized_transport}"
            ) from exc

    def _validate_input(
        self,
        employees: pd.DataFrame,
    ) -> None:
        missing_columns = (
            self.REQUIRED_COLUMNS
            - set(employees.columns)
        )

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise ValueError(
                "Colonnes nécessaires au calcul "
                f"des distances manquantes : {missing}"
            )
