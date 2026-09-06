# Tieout's API, and the fake company it investigates.
#
# This file sits at the REPO ROOT on purpose. Dokku picks a builder by looking at
# the root of the pushed repo: with no Dockerfile there it falls back to herokuish,
# finds no language marker in a monorepo root, and fails with "Unable to select a
# buildpack". A root Dockerfile makes the choice for it, so a plain git deploy
# works with no `builder:set` on the server.
#
# One container runs everything server-side: the ERP (:8701), the VendorLink portal
# (:8702) and the AP mailbox (:8703) are started by the API itself on loopback, and
# only the API port is published. The engine drives a real Chromium against that
# portal, which is why this image is built on Playwright's own base rather than a
# plain python image — the browser and its ~90 system libraries are already there.
#
# The desk is the second app and has its own Dockerfile at `desk/Dockerfile`.
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # The demo world and the engine store live on the container filesystem. That is
    # deliberate: a redeploy resets the demo to the seed, which is exactly what a
    # judge opening the link for the first time should see.
    TIEOUT_HOME=/data/tieout \
    # Never a visible browser on a server. The desk shows the portal through the
    # screenshots the engine saves, which is better on camera anyway.
    HEADLESS=1

WORKDIR /app

# Paths are repo-root relative: the build context is the repo root.
# Dependencies first so a code edit does not reinstall the world.
# pyproject declares no readme, so this is the only file the dependency layer needs.
# setuptools is told to find packages under src/, so that directory has to exist
# even here — empty is correct, this pass installs the dependencies and nothing else.
COPY backend/pyproject.toml ./
RUN mkdir -p src && pip install --no-cache-dir .

# Then the source, and the project itself.
COPY backend/src ./src
RUN pip install --no-cache-dir --no-deps .

# The base image ships Chromium matching its own Playwright version, and pyproject
# asks for `playwright>=1.45`, which that version already satisfies — pip leaves it
# alone, so the browser still matches. This line is the seatbelt: if the versions
# ever drift it fetches the right build, and if they do not it is a no-op.
RUN playwright install chromium

RUN mkdir -p /data/tieout

EXPOSE 8700

# Dokku hands the port in as $PORT and expects the process on 0.0.0.0, not loopback.
CMD ["sh", "-c", "python -m tieout.api --host 0.0.0.0 --port ${PORT:-8700}"]
