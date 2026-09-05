"""Test fixtures: a throwaway world, in a pinned month, in a temp database."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def temp_world(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Never touch ~/.tieout during tests, and pin the month so failures reproduce."""
    db = tmp_path_factory.mktemp("world") / "world.db"
    os.environ["TIEOUT_WORLD_DB"] = str(db)
    os.environ["TIEOUT_SEED_MONTH"] = "2026-09"

    from tieout.world import seed

    seed.reset_world()
    yield db

    os.environ.pop("TIEOUT_WORLD_DB", None)
    os.environ.pop("TIEOUT_SEED_MONTH", None)
