# Dockerfile : build le Portal (Vite + React + @lastarter/ui).
FROM node:22-alpine AS builder

WORKDIR /app

COPY packages/ui/package.json packages/ui/
COPY packages/ui/src packages/ui/src/
COPY packages/i18n/package.json packages/i18n/
COPY packages/i18n/src packages/i18n/src/
COPY packages/config/package.json packages/config/
COPY packages/config/src packages/config/src/
COPY apps/portal/package.json apps/portal/

RUN cd apps/portal && npm install --legacy-peer-deps

COPY apps/portal apps/portal
RUN cd apps/portal && npx vite build

FROM nginx:1.25-alpine
COPY --from=builder /app/apps/portal/dist /usr/share/nginx/html
EXPOSE 80
