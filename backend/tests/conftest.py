"""Test fixtures: a throwaway world on real ports, and an engine that never calls the model.

The world runs as three real uvicorn servers on free ports, not as in-process ASGI apps,
because one of the three sources is a browser and a browser needs a socket. That also means
every test exercises the same HTTP path the demo does.

``MODEL_API_KEY`` is emptied for the whole session, so ``pytest`` is offline and
deterministic: the engine falls back to the prose it writes itself, and the checklists,
confidences and rules — the parts that must be reproducible — are unaffected.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn

STARTUP_TIMEOUT_SECONDS = 20.0


@pytest.fixture(scope="session", autouse=True)
def temp_world(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Path]:
    """Never touch ~/.tieout during tests, and pin the month so failures reproduce."""
    home = tmp_path_factory.mktemp("tieout-home")
    os.environ["TIEOUT_HOME"] = str(home)
    os.environ["TIEOUT_WORLD_DB"] = str(home / "world.db")
    os.environ["TIEOUT_SEED_MONTH"] = "2026-09"
    os.environ["MODEL_API_KEY"] = ""  # tests never call a language model
    os.environ["HEADLESS"] = "1"

    from tieout.world import seed

    seed.reset_world()
    yield home

    for key in (
        "TIEOUT_HOME",
        "TIEOUT_WORLD_DB",
        "TIEOUT_SEED_MONTH",
        "MODEL_API_KEY",
        "HEADLESS",
    ):
        os.environ.pop(key, None)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def world_urls(temp_world: Path) -> Iterator[dict[str, str]]:
    """The ERP, the portal and the AP mailbox, live on free ports for the whole session."""
    from tieout.world.erp import app as erp_app
    from tieout.world.inbox import app as inbox_app
    from tieout.world.portal import app as portal_app

    apps = {"erp": erp_app, "portal": portal_app, "inbox": inbox_app}
    servers: dict[str, uvicorn.Server] = {}
    urls: dict[str, str] = {}
    for name, app in apps.items():
        port = _free_port()
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", access_log=False)
        )
        servers[name] = server
        urls[name] = f"http://127.0.0.1:{port}"
        threading.Thread(target=server.run, name=f"test-{name}", daemon=True).start()

    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline and not all(s.started for s in servers.values()):
        time.sleep(0.05)
    if not all(server.started for server in servers.values()):
        pytest.fail("the test world did not start")

    yield urls

    for server in servers.values():
        server.should_exit = True


@pytest.fixture(autouse=True)
def clean_store(temp_world: Path) -> Iterator[None]:
    """Every test starts with Tieout remembering nothing: no packs, decisions or rules."""
    from tieout.engine import store

    store.reset()
    yield
    store.reset()


@pytest.fixture
def sources(world_urls: dict[str, str]) -> Iterator[object]:
    from tieout.engine.investigate import Sources
    from tieout.engine.sources.erp import ErpClient
    from tieout.engine.sources.inbox import InboxClient

    with ErpClient(world_urls["erp"]) as erp, InboxClient(world_urls["inbox"]) as inbox:
        yield Sources(erp=erp, inbox=inbox, portal_base_url=world_urls["portal"], use_portal=True)


@pytest.fixture
def cases(world_urls: dict[str, str]) -> dict[str, object]:
    """The exceptions, found by the real three-way match. Never read from the seed."""
    from tieout.engine import match, store
    from tieout.engine.sources.erp import ErpClient

    with ErpClient(world_urls["erp"]) as erp:
        found = match.run(erp)
    store.save_exceptions(found)
    return {case.id: case for case in found}


def chromium_or_skip() -> None:
    """A missing browser is an environment problem, not a failing product."""
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:  # any launch failure means the same thing to a test run
        pytest.skip(f"chromium is not installed for Playwright: {exc}")
