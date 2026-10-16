# LaStarter Shell — Transfers.
# Build le shell React (sidebar Element Web + iframe de l'app originale).
# Sert le shell statique sur / et proxy l'app originale sur /app/.

FROM node:22-alpine AS builder

WORKDIR /app

# Copier le workspace pnpm (ui + shell)
COPY ../../packages/ui/package.json packages/ui/
COPY ../../packages/ui/src packages/ui/src/
COPY shells/transfers/package.json shells/transfers/

RUN cd shells/transfers && npm install --legacy-peer-deps

COPY shells/transfers shells/transfers

RUN cd shells/transfers && npx vite build

# ---- Runtime : nginx sert le shell + proxy ----
FROM nginx:1.25-alpine

COPY --from=builder /app/shells/transfers/dist /usr/share/nginx/html
COPY shells/transfers/nginx-shell.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
