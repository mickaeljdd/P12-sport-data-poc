from pathlib import Path

import pandas as pd
import pytest

from services.distance_cache import (
    DistanceCache,
)


def test_returns_none_when_address_is_unknown(
    tmp_path: Path,
):
    cache = DistanceCache(
        tmp_path / "cache.csv"
    )

    assert (
        cache.get(
            "10 rue Victor Hugo"
        )
        is None
    )


def test_saves_and_returns_distance(
    tmp_path: Path,
):
    cache = DistanceCache(
        tmp_path / "cache.csv"
    )

    cache.set(
        "10 rue Victor Hugo",
        12.5,
    )

    assert (
        cache.get(
            "10 rue Victor Hugo"
        )
        == 12.5
    )


def test_address_normalization_avoids_duplicates(
    tmp_path: Path,
):
    cache = DistanceCache(
        tmp_path / "cache.csv"
    )

    cache.set(
        "10 Rue Victor Hugo",
        12.5,
    )

    result = cache.get(
        "  10   rue VICTOR hugo  "
    )

    assert result == 12.5
    assert len(cache) == 1


def test_existing_distance_is_updated(
    tmp_path: Path,
):
    cache = DistanceCache(
        tmp_path / "cache.csv"
    )

    cache.set(
        "10 rue Victor Hugo",
        12.5,
    )

    cache.set(
        "10 rue Victor Hugo",
        13.2,
    )

    assert (
        cache.get(
            "10 rue Victor Hugo"
        )
        == 13.2
    )

    assert len(cache) == 1


def test_cache_is_persistent(
    tmp_path: Path,
):
    cache_path = (
        tmp_path / "cache.csv"
    )

    first_cache = DistanceCache(
        cache_path
    )

    first_cache.set(
        "10 rue Victor Hugo",
        12.5,
    )

    second_cache = DistanceCache(
        cache_path
    )

    assert (
        second_cache.get(
            "10 rue Victor Hugo"
        )
        == 12.5
    )


def test_negative_distance_is_rejected(
    tmp_path: Path,
):
    cache = DistanceCache(
        tmp_path / "cache.csv"
    )

    with pytest.raises(
        ValueError,
        match="négative",
    ):
        cache.set(
            "10 rue Victor Hugo",
            -1,
        )


def test_invalid_cache_file_is_rejected(
    tmp_path: Path,
):
    cache_path = (
        tmp_path / "cache.csv"
    )

    pd.DataFrame(
        {
            "Mauvaise colonne": [
                "valeur"
            ]
        }
    ).to_csv(
        cache_path,
        index=False,
    )

    with pytest.raises(
        ValueError,
        match="Colonnes manquantes",
    ):
        DistanceCache(
            cache_path
        )