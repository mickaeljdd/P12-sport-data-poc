from __future__ import annotations

from services.google_maps_distance_service import (
    GoogleMapsDistanceService,
)


def main() -> None:
    service = GoogleMapsDistanceService()

    # Remplacer uniquement par une adresse de test.
    # Évite d'afficher une véritable adresse RH dans les logs.
    test_address = "1 place de la Comédie, 34000 Montpellier, France"

    distance_km = service.get_distance_km(
        test_address
    )

    print(
        "Connexion Google Routes réussie."
    )
    print(
        f"Distance calculée : {distance_km:.2f} km"
    )


if __name__ == "__main__":
    main()