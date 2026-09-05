"""The fake company: ERP, vendor portal, inbox. A fixture, not the product."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import seed


@asynccontextmanager
async def seeded_lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Every service in the world seeds the database on first start, then serves it."""
    seed.ensure_world()
    yield
