"""PHASE 3 — the thin web layer over the engine.

Three files and no decisions of its own:

* ``schemas.py``  the request and response shapes the desk types against.
* ``runner.py``   starts ``engine.investigate.work`` on a thread and fans the engine's own
                  ``Event`` objects out to every open SSE stream.
* ``main.py``     eight routes, each of which reads the engine or the store and returns it.

There is no rule, no threshold, no browser call and no model call anywhere in this package.
Everything that decides anything lives in ``engine/``; if a line here starts to look like a
judgement, it is in the wrong folder.
"""

from __future__ import annotations

PORT = 8700
