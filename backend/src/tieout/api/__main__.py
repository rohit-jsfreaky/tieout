"""Run the API.

    python -m tieout.api            # :8700, and the fake company with it
    python -m tieout.api --verbose  # with uvicorn's access log

It starts the ERP, the vendor portal and the AP mailbox itself unless they are already
running, so ``curl`` alone is enough to drive all four beats.
"""

from __future__ import annotations

import argparse

import uvicorn

from . import PORT
from .main import app

HOST = "127.0.0.1"


def _banner(host: str, port: int) -> str:
    base = f"http://{host}:{port}"
    lines = [
        "",
        "  Tieout is listening. Nine routes, no logic.",
        "",
        f"    GET  {base}/queue",
        f"    GET  {base}/exceptions/E1",
        f"    POST {base}/exceptions/E1/work",
        f"    GET  {base}/exceptions/E1/events        (curl -N)",
        f'    POST {base}/exceptions/E1/decide        {{"action":"approve","by":"..."}}',
        f"    GET  {base}/policies",
        f"    GET  {base}/metrics",
        f"    POST {base}/reset",
        f"    GET  {base}/screenshots/E1-PO-1042.png",
        "",
        f"  Docs: {base}/docs",
        "",
    ]
    return "\n".join(lines)


def serve(host: str = HOST, port: int = PORT, verbose: bool = False) -> int:
    print(_banner(host, port), flush=True)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if verbose else "warning",
        access_log=verbose,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tieout.api",
        description="The Tieout API: queue, evidence, decisions, policies, metrics.",
    )
    parser.add_argument("--host", default=HOST, help=f"bind address (default {HOST})")
    parser.add_argument("--port", type=int, default=PORT, help=f"port (default {PORT})")
    parser.add_argument("--verbose", action="store_true", help="show uvicorn access logs")
    args = parser.parse_args(argv)
    return serve(host=args.host, port=args.port, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
