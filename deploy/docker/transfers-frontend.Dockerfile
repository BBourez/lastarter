# Dockerfile : build le frontend Transfers (Vite + React + @lastarter/ui).
FROM node:22-alpine AS builder

WORKDIR /app

# Copier les workspaces
COPY packages/ui/package.json packages/ui/
COPY packages/ui/src packages/ui/src/
COPY packages/i18n/package.json packages/i18n/
COPY packages/i18n/src packages/i18n/src/
COPY packages/config/package.json packages/config/
COPY packages/config/src packages/config/src/
COPY apps/transfers/package.json apps/transfers/

# Installer les dependances du frontend
RUN cd apps/transfers && npm install --legacy-peer-deps

# Copier le code source et builder
COPY apps/transfers apps/transfers
RUN cd apps/transfers && npx vite build

# Runtime : nginx sert le build statique
FROM nginx:1.25-alpine
COPY --from=builder /app/apps/transfers/dist /usr/share/nginx/html
COPY deploy/docker/transfers-nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
