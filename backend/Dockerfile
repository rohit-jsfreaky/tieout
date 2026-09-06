# Tieout's API, and the fake company it investigates.
#
# One container runs everything server-side: the ERP (:8701), the VendorLink portal
# (:8702) and the AP mailbox (:8703) are started by the API itself on loopback, and
# only the API port is published. The engine drives a real Chromium against that
# portal, which is why this image is built on Playwright's own base rather than a
# plain python image — the browser and its ~90 system libraries are already there.
#
# Base registry note: Pannly's Dockerfile pulls python from public.ecr.aws because
# the Hetzner build host cannot reach registry-1.docker.io. That does not apply here:
# this image is built on GitHub's runners and pushed to GHCR, and mcr.microsoft.com
# is neither Docker Hub nor rate-limited. Dokku only ever pulls the finished image.
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

# Dependencies first so a code edit does not reinstall the world.
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# Then the source, and the project itself.
COPY src ./src
RUN pip install --no-cache-dir --no-deps .

RUN mkdir -p /data/tieout

EXPOSE 8700

# Dokku hands the port in as $PORT and expects the process on 0.0.0.0, not loopback.
CMD ["sh", "-c", "python -m tieout.api --host 0.0.0.0 --port ${PORT:-8700}"]
