# Multi-environnements & multi-clients

## Comment ça marche

Le CLI génère automatiquement tous les sous-domaines à partir du domaine de base.

### Production (`lastarter.app`)

```bash
cd cli
python -m lastarter_cli init --client prod --domain lastarter.app --bricks drive,messages,chat,meet
python -m lastarter_cli deploy --client prod --pull
```

Génère :
- `id.lastarter.app` — SSO Keycloak
- `drive.lastarter.app` — Drive
- `messages.lastarter.app` — Messages
- `chat.lastarter.app` — Chat
- `meet.lastarter.app` — Visioconférence (element-call)
- `matrix.lastarter.app` — Synapse (backend chat)
- `transfers.lastarter.app` — Transfert de fichiers

### Démo (`demo.lastarter.app`)

```bash
python -m lastarter_cli init --client demo --domain demo.lastarter.app --bricks drive,messages,chat,meet
python -m lastarter_cli deploy --client demo --pull
```

Génère :
- `id.demo.lastarter.app`
- `drive.demo.lastarter.app`
- `messages.demo.lastarter.app`
- `chat.demo.lastarter.app`
- `meet.demo.lastarter.app`
- etc.

### Client spécifique (`acme.com`)

```bash
python -m lastarter_cli init --client acme --domain acme.com --bricks drive,messages,chat
python -m lastarter_cli deploy --client acme --pull
```

Chaque client = un projet Docker Compose indépendant (conteneurs, réseaux, volumes isolés).

## DNS requis

| Environnement | Enregistrement DNS | Type |
|---|---|---|
| Prod | `lastarter.app` + `*.lastarter.app` | A/AAAA + wildcard |
| Démo | `demo.lastarter.app` + `*.demo.lastarter.app` | A/AAAA + wildcard |
| Client | `acme.com` + `*.acme.com` | A/AAAA + wildcard |

Le wildcard `*.` couvre tous les sous-domaines générés par le CLI.

## TLS / Certificats

### POC / Démo interne
Le CLI génère automatiquement une CA locale + certificat wildcard.

### Production
Configurez Let's Encrypt avec DNS-01 (wildcard) :

```bash
certbot certonly --dns-cloudflare \
  -d lastarter.app -d "*.lastarter.app" \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini
```

Puis montez les certificats dans la passerelle (remplacez la CA POC).

## Reset automatique (démo toutes les 3 mois)

```bash
# Crontab : 0 3 1 */3 * = 1er du mois, tous les 3 mois à 3h du matin
0 3 1 */3 * /path/to/lastarter/scripts/reset-demo.sh demo demo.lastarter.app
```

Le script :
1. Arrête tous les conteneurs
2. Supprime les volumes (bases de données, médias)
3. Supprime la configuration et les secrets
4. Régénère avec des **credentials neufs** (automatique)
5. Redéploie completement

## Credentials par environnement

Chaque environnement a son propre `secrets.env` :
- `deployments/prod/secrets.env`
- `deployments/demo/secrets.env`
- `deployments/acme/secrets.env`

Tous les secrets (mots de passe, clés API, tokens) sont uniques par environnement.

## Coexistence

Plusieurs environnements peuvent tourner sur le même serveur :

```bash
python -m lastarter_cli ps --client prod    # conteneurs prod
python -m lastarter_cli ps --client demo    # conteneurs démo
python -m lastarter_cli ps --client acme    # conteneurs client acme
```

Chaque client a son propre réseau Docker (`lastarter-prod`, `lastarter-demo`, `lastarter-acme`).
