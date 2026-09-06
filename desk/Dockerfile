# The desk. A thin client — it renders what the API returns and holds no logic.
#
# NEXT_PUBLIC_API_BASE is read at BUILD time by Next, so it arrives as a build arg
# rather than a runtime env var. If it is wrong after deploy there is no need to
# rebuild: lib/api.ts also reads an override out of localStorage, so the API base
# can be repointed from the browser.
FROM public.ecr.aws/docker/library/node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM public.ecr.aws/docker/library/node:22-slim AS build
WORKDIR /app
ARG NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# `output: standalone` is set in next.config.ts so this stage copies a self-contained
# server instead of the whole node_modules tree.
FROM public.ecr.aws/docker/library/node:22-slim AS run
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
COPY --from=build /app/public ./public

EXPOSE 3000

# Next's standalone server reads PORT and HOSTNAME from the environment.
CMD ["sh", "-c", "HOSTNAME=0.0.0.0 PORT=${PORT:-3000} node server.js"]
