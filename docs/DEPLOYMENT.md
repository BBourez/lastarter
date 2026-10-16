# Deploiement LaStarter

## Prerequis

- Docker + Docker Compose (ou Kubernetes)
- Node.js >= 22 + pnpm >= 9 (pour le build)
- Un domaine avec DNS wildcard `*.<domaine>` pointant vers le serveur

## Quick start (Docker Compose)

### 1. Configurer l'environnement

```bash
cp .env.example .env
# Editer .env : domaine, mots de passe, modules actifs
```

### 2. Deployer le core (SSO + passerelle)

```bash
docker compose -f deploy/docker/core.yml up -d
```

### 3. Deployer les modules souhaites

```bash
# Transfers
docker compose -f deploy/docker/transfers.yml up -d

# Projects
docker compose -f deploy/docker/projects.yml up -d
```

### 4. Verifier

```bash
curl https://id.<domaine>/realms/lastarter/.well-known/openid-configuration
curl https://<domaine>/
```

## Kubernetes (Helm)

```bash
# Installer le chart
helm install lastarter deploy/kubernetes/ \
  --set domain=acme.com \
  --set keycloak.dbPassword=change-me \
  --set transfers.enabled=true \
  --set projects.enabled=true

# Mettre a jour
helm upgrade lastarter deploy/kubernetes/ \
  --set domain=acme.com
```

## Configuration .env

| Variable | Description | Defaut |
|---|---|---|
| LASTARTER_DOMAIN | Domaine principal | localhost:8443 |
| LASTARTER_SCHEME | HTTP/HTTPS | https |
| MODULE_TRANSFERS | Activer Transfers | true |
| MODULE_PROJECTS | Activer Projects | true |
| MODULE_CHAT | Activer Discussions | true |
| MODULE_MEET | Activer Reunions | true |
| KC_DB_PASSWORD | Mot de passe PostgreSQL Keycloak | (a definir) |
| KC_ADMIN_PASSWORD | Mot de passe admin Keycloak | (a definir) |
| TRANSFERS_DB_PASSWORD | Mot de passe PostgreSQL Transfers | (a definir) |

## Certificats TLS

### POC (developpement)

CA locale auto-generee par le CLI :
```bash
certutil -user -addstore Root "certs/ca.crt"  # Windows
sudo cp certs/ca.crt /usr/local/share/ca-certificates/  # Linux
```

### Production

Let's Encrypt avec DNS-01 (wildcard) :
```bash
certbot certonly --dns-cloudflare \
  -d acme.com -d "*.acme.com" \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini
```

## Mise a jour

```bash
# Recuperer les dernieres images
docker compose -f deploy/docker/core.yml pull
docker compose -f deploy/docker/transfers.yml pull

# Redemarrer
docker compose -f deploy/docker/core.yml up -d
docker compose -f deploy/docker/transfers.yml up -d
```

## Backup

```bash
# Sauvegarder les volumes
docker run --rm -v lastarter_kc_pgdata:/data -v $(pwd):/backup alpine \
  tar czf /backup/keycloak-backup.tar.gz -C /data .

# Restaurer
docker run --rm -v lastarter_kc_pgdata:/data -v $(pwd):/backup alpine \
  tar xzf /backup/keycloak-backup.tar.gz -C /data
```

## Securite

- Toutes les bases de donnees sont en reseau interne (pas de ports exposes)
- Les secrets sont dans `.env` (gitignore)
- Les access S3 sont generes automatiquement par le CLI
- Pas de port 5432/6379/9000 exposes publiquement
