# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

FROM node:22-slim AS base

RUN npm install -g bun

WORKDIR /app

# Install dependencies
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

# Build
COPY . .

ARG BASE_PATH=/svelte
ENV BASE_PATH=${BASE_PATH}

RUN bun run build

# Production image
FROM node:22-slim AS production

WORKDIR /app

COPY --from=base /app/build ./build
COPY --from=base /app/package.json ./
COPY --from=base /app/node_modules ./node_modules

ENV PORT=3000
ENV BASE_PATH=/svelte

EXPOSE 3000

CMD ["node", "build/index.js"]
