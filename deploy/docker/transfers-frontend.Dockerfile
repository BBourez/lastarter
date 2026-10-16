# Dockerfile : build le frontend Transfers avec pnpm workspace.
FROM node:22-alpine AS builder

RUN corepack enable

WORKDIR /app

# Copier les manifests workspace
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ui/package.json packages/ui/
COPY packages/i18n/package.json packages/i18n/
COPY packages/api/package.json packages/api/
COPY packages/config/package.json packages/config/
COPY apps/transfers/package.json apps/transfers/

RUN pnpm install --no-frozen-lockfile

COPY packages/ui packages/ui
COPY packages/i18n packages/i18n
COPY packages/api packages/api
COPY packages/config packages/config
COPY apps/transfers apps/transfers

RUN cd apps/transfers && npx vite build

FROM nginx:1.25-alpine
COPY --from=builder /app/apps/transfers/dist /usr/share/nginx/html
COPY deploy/docker/transfers-nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
