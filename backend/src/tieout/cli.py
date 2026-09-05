"""The `tieout` command.

Phase 1 wires up the two commands the world needs. The engine's commands (`match`, `work`,
`decide`, `policies`, `metrics`, `demo`) are added in Phase 2, as subparsers alongside these.
"""

from __future__ import annotations

import argparse

from .world import __main__ as world_main


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tieout",
        description="An agent that only works the invoices that broke.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    world = commands.add_parser("world", help="run the fake company (ERP, portal, inbox)")
    world.add_argument("--fresh", action="store_true", help="reseed the world before serving")
    world.add_argument("--host", default=world_main.HOST, help="bind address")
    world.add_argument("--verbose", action="store_true", help="show uvicorn access logs")

    commands.add_parser("reset", help="put the world back to the seed")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "world":
        if args.fresh:
            world_main.seed.reset_world()
        return world_main.serve(host=args.host, verbose=args.verbose)
    if args.command == "reset":
        return world_main.reset()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
