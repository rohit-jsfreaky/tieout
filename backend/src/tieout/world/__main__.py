"""Run the whole fake company with one command.

    python -m tieout.world            # ERP :8701, portal :8702, inbox :8703
    python -m tieout.world --fresh    # reseed first, then serve
    python -m tieout.world --reset    # reseed and exit

Three uvicorn servers, one per thread, one process. Ctrl+C stops all three.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass

import uvicorn

from . import erp, inbox, portal, seed

HOST = "127.0.0.1"
STARTUP_TIMEOUT_SECONDS = 15.0


@dataclass(frozen=True)
class Service:
    name: str
    app: object
    port: int
    opens_at: str


SERVICES: tuple[Service, ...] = (
    Service("ERP", erp.app, erp.PORT, "/invoices"),
    Service("Portal", portal.app, portal.PORT, "/login"),
    Service("Inbox", inbox.app, inbox.PORT, "/threads"),
)


def _server(service: Service, host: str, verbose: bool) -> uvicorn.Server:
    config = uvicorn.Config(
        service.app,
        host=host,
        port=service.port,
        log_level="info" if verbose else "warning",
        access_log=verbose,
    )
    return uvicorn.Server(config)


def _banner(host: str) -> str:
    user, password = seed.portal_credentials()
    lines = [
        "",
        f"  {seed.COMPANY_NAME} is open for business.",
        "",
    ]
    for service in SERVICES:
        lines.append(f"  {service.name:<7} http://{host}:{service.port}{service.opens_at}")
    lines += [
        "",
        f"  Portal sign-in: {user} / {password}",
        f"  Try: curl http://{host}:{erp.PORT}/invoices",
        f"       curl 'http://{host}:{inbox.PORT}/threads?po=PO-1042'",
        f"       open http://{host}:{portal.PORT}/orders/PO-1042/delivery-note",
        "",
        "  Ctrl+C to stop.",
        "",
    ]
    return "\n".join(lines)


@dataclass
class Running:
    """Three live services on daemon threads, and the handle that stops them."""

    servers: list[uvicorn.Server]
    threads: list[threading.Thread]

    @property
    def alive(self) -> bool:
        return any(thread.is_alive() for thread in self.threads)

    def stop(self) -> None:
        for server in self.servers:
            server.should_exit = True
        for thread in self.threads:
            thread.join(timeout=5)


class WorldNotStarted(RuntimeError):
    """A port was busy. Better to say so than to serve half a company."""


def start_background(host: str = HOST, verbose: bool = False) -> Running:
    """Start all three services without blocking. ``tieout demo`` runs the world this way."""
    seed.ensure_world()
    servers = [_server(service, host, verbose) for service in SERVICES]
    threads = [
        threading.Thread(target=server.run, name=service.name, daemon=True)
        for server, service in zip(servers, SERVICES, strict=True)
    ]
    for thread in threads:
        thread.start()

    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline and not all(server.started for server in servers):
        if not any(thread.is_alive() for thread in threads):
            break
        time.sleep(0.05)

    running = Running(servers=servers, threads=threads)
    if not all(server.started for server in servers):
        stalled = ", ".join(
            service.name
            for service, server in zip(SERVICES, servers, strict=True)
            if not server.started
        )
        running.stop()
        raise WorldNotStarted(f"Could not start: {stalled}. Is the port already in use?")
    return running


def serve(host: str = HOST, verbose: bool = False) -> int:
    """Start all three services and block until interrupted."""
    try:
        running = start_background(host=host, verbose=verbose)
    except WorldNotStarted as exc:
        print(str(exc), flush=True)
        return 1

    print(_banner(host), flush=True)
    try:
        while running.alive:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n  Closing the office.", flush=True)
    finally:
        running.stop()
    return 0


def reset() -> int:
    """Put every table back to the seed. Nothing else in the world is stateful."""
    path = seed.reset_world()
    print(json.dumps(seed.summary(path), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tieout.world",
        description="Run the fake company: ERP, vendor portal and AP mailbox.",
    )
    parser.add_argument("--reset", action="store_true", help="reseed the world and exit")
    parser.add_argument("--fresh", action="store_true", help="reseed the world, then serve")
    parser.add_argument("--host", default=HOST, help=f"bind address (default {HOST})")
    parser.add_argument("--verbose", action="store_true", help="show uvicorn access logs")
    args = parser.parse_args(argv)

    if args.reset:
        return reset()
    if args.fresh:
        seed.reset_world()
    return serve(host=args.host, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
