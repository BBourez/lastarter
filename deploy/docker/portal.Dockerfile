# Dockerfile : build le Portal avec pnpm workspace.
FROM node:22-alpine AS builder

RUN corepack enable

WORKDIR /app

# Copier les manifests workspace
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY packages/ui/package.json packages/ui/
COPY packages/i18n/package.json packages/i18n/
COPY packages/config/package.json packages/config/
COPY apps/portal/package.json apps/portal/

# Installer les dependances (workspace complet)
RUN pnpm install --no-frozen-lockfile

# Copier le code source
COPY packages/ui packages/ui
COPY packages/i18n packages/i18n
COPY packages/config packages/config
COPY apps/portal apps/portal

# Builder le portal
RUN cd apps/portal && npx vite build

# Runtime : nginx sert le build statique
FROM nginx:1.25-alpine
COPY --from=builder /app/apps/portal/dist /usr/share/nginx/html
EXPOSE 80
