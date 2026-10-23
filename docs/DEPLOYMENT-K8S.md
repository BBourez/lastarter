# Déploiement Kubernetes (kind) — phase 5

Cible de validation locale : un cluster kind mono-nœud (`kind-lastarter`) avec
ingress-nginx. Première tranche VALIDÉE : **Keycloak** (realm as-code, importé
au premier boot) + brique **Drive** (chart amont pinné), fumée curl verte à
travers l'ingress. Le stack compose `demo-coop` reste le produit de référence ;
cette page décrit la cible k8s et ses écarts assumés.

## Prérequis

- `kubectl` 1.36+
- `kind` + `helm` (v4) — binaires locaux attendus dans `%USERPROFILE%/.lastarter-bin/`
- le chart drive amont en **lecture seule** : `../examples/drive/src/helm/drive`
  (relatif au dépôt ; surchargeable par `CHART_DRIVE`)

## Architecture validée

Namespace unique `lastarter` :

| Composant | Manifest / chart | Notes |
| --- | --- | --- |
| PostgreSQL 18-alpine | `manifests/10-postgres.yaml` | raw, PVC 2Gi, une instance / deux bases (keycloak, drive) via initdb SQL |
| Valkey 8.1-alpine | `manifests/11-valkey.yaml` | raw, sans état (comme compose) |
| RustFS 1.0.3 | `manifests/12-rustfs.yaml` | raw, PVC 5Gi, Service `rustfs` (DNS sans underscore) |
| Bucket S3 | `manifests/13-s3-init.yaml` | Job one-shot `amazon/aws-cli:2.27.48` : `drive-media-storage` + versioning |
| Keycloak 26.8.1 | `manifests/20-keycloak.yaml` | `start-dev --import-realm`, realm + thème montés en Secret |
| Brique Drive | chart amont + `values-drive.yaml` | images `lasuite/drive-{backend,frontend}:v0.25.2` |

Ingress (POC **HTTP**, ports hôtes kind : 8080 -> 80) :

- `id.localhost` -> svc `keycloak:8080` (`manifests/30-ingress-id.yaml`)
- `drive.localhost` -> frontend (/) + backend (`/api`, `/external_api`, `/admin`,
  `/media`) — ingresses rendus par le chart amont depuis `values-drive.yaml`

Rendus à secrets (jamais commités, `deploy/k8s/.runtime/`, gitignoré) :
générés par `deploy/k8s/kind/render-realm.py` qui **réutilise le moteur du CLI
compose** (`cli.lastarter_cli.cmd.deploy` : `build_realm_clients` + `render_realm`)
sur le gabarit committé `identity/realm-lastarter.json`. Le scheme du moteur est
forcé à `http` et le domaine porté (`localhost:8080`) pour produire des origins
k8s (`http://drive.localhost:8080`, …) au lieu des origins compose (`:8443`) ;
les secrets clients OIDC sont générés à neuf (aucune valeur du coffre compose ne
traverse ici). Idempotent : les valeurs existantes de `.runtime/secrets.env`
sont réutilisées telles quelles (invariant CLI, append-only).

## Étapes exactes validées

```bash
# 0. Cluster kind + ingress-nginx (déjà en place sur la machine de validation)
export PATH="$HOME/.lastarter-bin:$PATH"
kind create cluster --name lastarter --config deploy/k8s/kind/kind-config.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx wait --for=condition=ready pod -l app.kubernetes.io/component=controller --timeout=300s

# 1. Tout le déploiement (idempotent, ré-exécutable)
bash deploy/k8s/deploy.sh
```

`deploy.sh` enchaîne : rendu realm+secrets (python) -> Secrets k8s rendus ->
manifests (postgres/valkey/rustfs/s3-init/keycloak/ingress) -> attente ready ->
`helm upgrade --install drive <chart amont> -f values-drive.yaml -f .runtime/values-drive-secrets.yaml`
-> attente rollouts. Garde-fou : refuse de tourner hors du contexte
`kind-lastarter` (jamais sur le Docker Desktop du compose).

## Fumée validée (sorties réelles)

```text
$ kubectl get pods -n lastarter
drive-backend-8485c594cf-mrtql                                    1/1   Running
drive-backend-celery-beat-9f55b5f8c-92sxz                         1/1   Running
drive-backend-celery-default-747f6f668b-b6v5q                     1/1   Running
drive-frontend-54468dfbff-d8w2q                                   1/1   Running
keycloak-6cc858dddb-jcb4h                                         1/1   Running
postgres-7b596f5665-wvf27                                         1/1   Running
rustfs-7c5d45f467-4rm5r                                           1/1   Running
s3-init-... / cronjob check-pending-malware-analysis-tasks-...    0/1   Completed
valkey-7bf84cdc67-4jfpd                                           1/1   Running
```

```text
$ curl -s -o /dev/null -w '%{http_code}' http://id.localhost:8080/realms/lastarter/.well-known/openid-configuration
200      # issuer: http://id.localhost:8080/realms/lastarter

$ curl -s -o /dev/null -w '%{http_code}' http://drive.localhost:8080/
200      # frontend drive

$ curl -s -L http://drive.localhost:8080/api/v1.0/authenticate/
-> 302 vers id.localhost:8080/realms/lastarter/protocol/openid-connect/auth
-> 200 : formulaire de login Keycloak (thème lastarter)
```

Chaîne SSO de bout en bout (curl, cookies Keycloak forcés en header — voir
limitation HTTP ci-dessous) : POST `demo/<mot de passe>` sur le formulaire ->
302 vers `/api/v1.0/callback/?...code=...` -> le backend échange le code via le
token endpoint **in-cluster** (`http://keycloak:8080/realms/lastarter/...`) ->
session drive authentifiée :

```text
$ curl -b jar http://drive.localhost:8080/api/v1.0/items/
{"count":0,"next":null,"previous":null,"results":[]}      # 200, session valide
```

Comptes (générés dans `deploy/k8s/.runtime/secrets.env`) :

- utilisateur démo : `demo` / `demo_user_password`
- console admin Keycloak (`http://id.localhost:8080`, realm `master`) : `admin` / `kc_admin_password`
- superuser Django drive (`http://drive.localhost:8080/admin`) : `admin@lastarter.local` / `drive_superuser_password`

## Limitations (honnêtes) et roadmap

- **POC HTTP :8080.** Keycloak 26 émet ses cookies de session `Secure;
  SameSite=None` même derrière un ingress HTTP : un navigateur ne les renvoie
  pas sur http, donc le login interactif dans le navigateur est bloqué. La
  chaîne OIDC complète (formulaire 200 + POST login + échange du code par le
  backend + session API) est validée par curl avec cookies forcés — artefact de
  test uniquement. **TLS sur l'ingress (cert-manager) = roadmap** ; il débloque
  le login navigateur et permet de revenir à `DJANGO_SETTINGS_MODULE=drive.settings`
  (Production stricte) en supprimant le ConfigMap `drive-settings-k8s`.
- **Module PocHTTP** (`manifests/40-drive-settings.yaml`) : Production adouci
  (SSL redirect, cookies Secure, HSTS retirés) pour l'HTTP local — monté via
  ConfigMap, zéro fork de l'image amont. Appliqué au seul déploiement web ;
  jobs/celery/cronjobs restent sur `drive.settings`/Production.
- **Secrets en clair dans `.runtime/`** : générés localement, gitignorés.
  Chiffrement (SOPS / external-secrets) = roadmap.
- **1 brique validée** (drive). Les autres (discussions, meet, docs) suivent le
  même schéma : chart amont quand il existe, sinon manifests ; leurs clients
  OIDC sont déjà présents dans le realm rendu (origins `http://*.localhost:8080`).
- **Une instance PostgreSQL, deux bases** (le compose préfère deux instances
  dédiées `kc_postgresql` / `drive_postgresql`).
- **Ingress média** (`/media/(.*)`) : pattern amont conservé (auth-url backend
  puis S3 rustfs), mais l'annotation `configuration-snippet` (CSP) est retirée
  (snippets nginx désactivés par défaut côté contrôleur) et le téléchargement
  média n'est pas couvert par la fumée de cette tranche.
- **Backchannels in-cluster** : les pods ne résolvent pas `*.localhost` ;
  l'endpoint d'autorisation OIDC est browser-facing (`http://id.localhost:8080`),
  jwks/token/userinfo/logout passent par le Service interne `keycloak:8080`.
- **Découverte amont** : `CELERY_BROKER_URL` est requis en plus de `REDIS_URL`
  (défaut amont `redis://redis:6379/0`) — le compose actuel ne le set pas ;
  signaler à l'amont ou au compose.

## Teardown

```bash
helm uninstall drive -n lastarter
kubectl delete namespace lastarter
# cluster entier :
kind delete cluster --name lastarter
```
