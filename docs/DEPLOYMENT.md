# Déploiement LaStarter

## Prérequis

| Besoin | Détail |
|---|---|
| Système | Linux (ou WSL2/macOS) avec bash ; Docker 24+ **avec plugin compose** (`docker compose version`) |
| Python | ≥ 3.12 — la CLI est stdlib-only, rien à installer |
| Réseau | Un domaine avec wildcard `*.<domaine>` pointant vers le serveur ; port **8443** (`EDGE_PORT`) ouvert |
| TLS | POC : CA locale générée par le CLI (à importer) · Production : certificat wildcard (DNS-01) |

## Démarrage

### Installateur une ligne

```bash
curl -fsSL https://raw.githubusercontent.com/BBourez/lastarter/main/install.sh | bash
```

Variables reconnues : `LASTARTER_HOME` (défaut `~/.lastarter`),
`LASTARTER_CLIENT`, `LASTARTER_DOMAIN`, `LASTARTER_APPS` (ex.
`drive,discussions,meet`), `LASTARTER_THEME`, `LASTARTER_LOGO`,
`LASTARTER_OUTPUT`, `LASTARTER_DEPLOY=1`. L'installateur est **idempotent** :
ré-exécuter met à jour le dépôt, rejoue `init` (pré-rempli, logo conservé)
et, si `LASTARTER_DEPLOY=1`, redéploie.

### Manuel

```bash
git clone https://github.com/BBourez/lastarter && cd lastarter/cli
python -m lastarter_cli init        # ou --non-interactive --client "ACME" \
                                    #    --domain acme.example.com --bricks drive,meet \
                                    #    --theme element-light --logo acme.svg
cd ..
PYTHONPATH=cli python -m lastarter_cli deploy --client acme --pull
PYTHONPATH=cli python -m lastarter_cli ps --client acme
```

## Cycle de vie d'un déploiement

| Commande | Rôle |
|---|---|
| `init` | questionnaire / rejeu pré-rempli → `deployments/<client>/` (manifeste, env, coffre, branding, SOURCES.md) |
| `deploy --client X --pull` | gates → rendu `.runtime/` (secrets, realm, thème, branding, configs natifs) → infra → migrations → `up -d --wait` |
| `ps --client X` | état des conteneurs |
| `smoke --client X` | surfaces HTTP (portail, SSO, apps) avec la CA du déploiement |
| `sbom --client X` | inventaire CycloneDX des briques épinglées |
| `deploy --client X --down` | arrêt (volumes conservés) |
| `detect [--domain …]` | audit d'environnement (Docker, ports, DNS, IP) |

Après un premier `deploy`, les surfaces servies :

| URL | Service |
|---|---|
| `https://id.<domaine>` | Keycloak (console admin : `admin` / secret `kc_admin_password`) |
| `https://<domaine>` | portail (tuiles des briques activées) |
| `https://chat.<domaine>` | Discussions (element-web + API Matrix same-origin) |
| `https://drive.<domaine>` | Drive |
| `https://meet.<domaine>` | Meet (visio) · `https://livekit.<domaine>` : websocket SFU |

## Opérations

### Sauvegarde / restauration

```bash
# Inventorier les volumes du projet
docker volume ls --format '{{.Name}}' | grep <slug-client>

# PostgreSQL — préféré (à chaud, cohérent) ; nom de conteneur visible dans `lastarter ps` :
docker exec -t <conteneur_kc_postgresql> pg_dump -U keycloak keycloak > kc-$(date +%F).sql

# Ou à froid (volume entier) :
docker run --rm -v <volume_pgdata>:/data -v "$PWD":/backup alpine tar czf /backup/pgdata.tgz -C /data .
# Restauration :
docker run --rm -v <volume_pgdata>:/data -v "$PWD":/backup alpine tar xzf /backup/pgdata.tgz -C /data
```

Le coffre `deployments/<client>/secrets.env` se sauvegarde **avec** les
volumes (sans lui, SSO et données ne sont plus relisibles) ; le chiffrer
(SOPS — roadmap) avant tout stockage externe.

### TLS / certificats

- **POC** : le CLI génère une CA locale + un certificat serveur
  (`deployments/<client>/.runtime/certs/`) au premier `deploy`. Importer
  `ca.crt` dans le magasin racine des postes (Windows :
  `certutil -user -addstore Root ca.crt`). Les SAN sont régénérés si le
  domaine change ; la CA, créée une fois, reste stable.
- **Production** : fournir un certificat wildcard reconnu (Let's Encrypt
  DNS-01, ex. `certbot certonly --dns-… -d domaine -d '*.domaine'`),
  remplacer `server.crt`/`server.key` du runtime puis redémarrer la
  passerelle. L'automatisation complète des certificats de production reste
  en [ROADMAP.md](ROADMAP.md).

### Montée de versions (pins)

1. `python -m lastarter_cli check-updates` — retards éventuels (le workflow
   hebdomadaire `upstream-sync` ouvre une PR avec les bumps proposés).
2. Relire les changelogs / breaking changes de l'amont (note de revue dans
   la PR).
3. Mettre à jour `catalogue/<brique>.toml` : `upstream_pin` **et** les images
   `[env]` concernées. synapse et livekit ne sont pas suivis automatiquement :
   leurs bumps sont manuels.
4. `deploy --client X --pull`.

⚠ **Postgres en version majeure** (ex. 14.3 → 18 pour la base Keycloak,
roadmap) : les volumes de données ne sont pas portables entre majeures —
`pg_dump` avant, `pg_restore` après, sinon le conteneur refuse de démarrer
sur un volume d'incompatibilité. Même prudence pour un bump Keycloak
(26.3.2 → 26.8.1 = roadmap) : tester d'abord sur un client de démo.

### Secrets

- Coffre `deployments/<client>/secrets.env` : généré une seule fois par
  `init`, croissance **append-only** (une nouvelle brique ajoute ses
  secrets, les valeurs existantes ne sont jamais réécrites), gitigné.
- Rotation : éditer la valeur puis `deploy --client X` (le rendu substitue
  à chaque déploiement) ; pour un secret OIDC, le client Keycloak
  correspondant est resynchronisé par l'API admin au déploiement suivant
  (idempotent).
- Chiffrement au repos (SOPS / ansible-vault) : roadmap.

## CI / veille

- [`ci.yml`](../.github/workflows/ci.yml) : tests CLI (Python 3.12/3.13),
  catalogue + gate licences, rendu `init` non interactif avec asserts.
- [`upstream-sync.yml`](../.github/workflows/upstream-sync.yml)
  (hebdomadaire) : veille amont → PR de bump à réviser avant fusion.
