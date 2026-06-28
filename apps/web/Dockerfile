# Bid Desk web — Next.js (App Router). Build context: REPO ROOT (needs the root
# pnpm-lock.yaml + pnpm-workspace.yaml + packages/shared-types + apps/web).
# pnpm via corepack, pinned to packageManager in root package.json.
FROM node:22-bookworm-slim AS base
ENV PNPM_HOME=/pnpm PATH="/pnpm:$PATH"
RUN corepack enable
WORKDIR /repo

# --- deps: install with the frozen lockfile (cached unless manifests change) ---
FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages/shared-types/package.json packages/shared-types/
COPY apps/web/package.json apps/web/
RUN pnpm install --frozen-lockfile

# --- build: next build is the gate (locked decision 3) ---
FROM base AS build
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages ./packages
COPY apps/web ./apps/web
# NEXT_PUBLIC_* is inlined at build time. Default targets the host-published AI port
# (lib/api.ts runs in the browser → reaches the backend via localhost:8000, not the
# compose-internal hostname). Override with --build-arg for a deployed base URL.
ARG NEXT_PUBLIC_AI_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_AI_BASE_URL=$NEXT_PUBLIC_AI_BASE_URL
RUN pnpm --filter @aerchain/web build

# --- runtime: next start on :3000 (non-standalone — next.config.mjs unchanged) ---
FROM base AS runtime
ENV NODE_ENV=production
COPY --from=build /repo/node_modules ./node_modules
COPY --from=build /repo/apps/web ./apps/web
COPY --from=build /repo/packages ./packages
COPY --from=build /repo/package.json /repo/pnpm-lock.yaml /repo/pnpm-workspace.yaml ./
USER node
EXPOSE 3000
CMD ["pnpm", "--filter", "@aerchain/web", "start"]
