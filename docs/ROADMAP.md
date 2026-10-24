# Feuille de route

Statut au 2026-10-23, après la reprise « briques amont vanilla » (retrait
total d'element-call ; drive et meet amont sans fork). Les intentions
historiques sont archivées dans [history/](history/).

## Kubernetes

- Cible : charts **amont** quand ils existent (meet publie un chart
  officiel), charts communautaires éprouvés sinon (synapse, keycloak) —
  cf. `deploy/k8s/README.md`.
- Secrets : external-secrets ou SOPS (fin du coffre en clair gitigné).
- Contrat inchangé : le manifeste client (`deployments/<client>/lastarter.toml`)
  détermine les sous-charts activés.

## Brique « docs » (documents collaboratifs)

- Amont : lasuite/impress — publié `PUBLISH_AS_MIT` (à revérifier au moment
  du chantier). Même modèle que drive/meet : images pinnées + intégration
  OIDC par env + theming natif, zéro fork. Ajout au registre
  [licences.md](licences.md) requis (gate).

## Messages / transfers

- Brique « messages » et transferts inter-apps de La Suite numérique :
  catégorisation, manifeste catalogue, compose, OIDC — même checklist
  qu'une nouvelle brique (`catalogue/SCHEMA.md`).

## MAS — matrix-authentication-service

- Introduire [MAS](https://github.com/element-hq/matrix-authentication-service)
  comme couche SSO dédiée à Matrix, en complément ou à la place de l'OIDC
  direct synapse ↔ Keycloak : Keycloak → MAS → synapse/element-web, session
  Matrix unifiée et délégation d'identité propre.

## Bumps différés (assumés)

| Cible | Pin actuel | Cible visée | Note |
|---|---|---|---|
| Keycloak | 26.3.2 | 26.8.1 | validé E2E sur 26.3.2 ; tester sur un client démo avant généralisation |
| Postgres (base Keycloak) | 14.3 | 18 | **migration de volume** obligatoire (pg_dump/restore) |
| synapse | v1.163.1 | — | suivi manuel (pas de champ `upstream_repo` propre) |
| livekit | v1.13.6 | — | suivi manuel |
| Redis (drive, meet) | 5 | 8 (ou valkey) | redis 5 = EOL ; choix actuel = versions des compose amonts (BSD, pré-7.4) — bump à rejouer sur un client démo (cache/broker, pas de volume de données critique) |

## Meet — chantiers restants

État honnête : meet est **déployée** (images amont suitenumerique, SSO,
theming CSS natif) et couverte par le smoke HTTP — mais son parcours client
complet (SSO → salon → invitation → appel) n'est pas encore validé par un e2e
rejouable.

- **Titre de l'app** : `VITE_APP_TITLE` est un build-arg amont (défaut
  « La Suite Meet ») — contournement à arbitrer : rebuild overlay
  `FROM` l'image amont, ou `sub_filter` edge.
- **e2e meet à réécrire** : les anciens scripts `meet.js` /
  `meet-invitation.js` (brique de visio précédente) ont été retirés ;
  réécrire le parcours SSO → création de salon → invitation → appel sur la
  brique suitenumerique.
- **TURN / UDP** : ni port hôte UDP (mux 7882) ni TURN en v1 — limitera les
  réseaux d'entreprise restrictifs.
- Exclus v1 (non déployés) : summary (lasuite/meet-summary), agents
  (lasuite/meet-agents), transcription/whisper, egress (enregistrements).

## Find inter-app

- Recherche transversale entre les briques (drive + discussions + future
  docs) : dépend de l'indexation côté amonts ; à cadrer.

## Divers

- Automatisation des certificats de production (DNS-01 dans la passerelle).
- Veille amont = `check-updates` + workflow [`upstream-sync`](../.github/workflows/upstream-sync.yml)
  (hebdomadaire). `renovate.json5` a été retiré : son customManager regex
  n'appariait jamais les TOML drive/meet (pas d'`upstream_image` adjacent à
  `upstream_pin`) et doublonnait la veille CI.

## Bumps livrés et validés en live (2026-10-23)

- **Keycloak 26.3.2 → 26.8.1** : catalogue + compose, déployé sur demo-coop (realm re-provisionné, smoke 8/8, e2e chat vert).
- **PostgreSQL keycloak 14.3 → 18-alpine** : volume réinitialisé + montage déplacé vers `/var/lib/postgresql` (nouveau layout des images postgres 18+, compatible `pg_upgrade`). Pour un client existant : `pg_dump`/`pg_restore` avant montée de version.
- **Redis 5 → Valkey 8.1-alpine** (drive, meet) : BSD-3, compatible RESP, déployé et healthy.
- **Brique Docs (lasuite/impress v6.0.3)** : ajoutée (catalogue, compose 11 services, licences) ; collaboration Yjs via yhub sans fork ; export PDF absent des images amont `PUBLISH_AS_MIT` (choix MIT assumé) ; recherche dédiée (brique Find) = roadmap.
- **Brique Find (lasuite/find) : NON-VIABLE le 2026-10-24** — l'amont n'a ni tag git ni tag Docker Hub versionné (seul `main` écrasé, projet pré-première-release ; procédure de release documentée mais jamais exécutée). Règle « toujours pinner » appliquée : brique non créée. Ré-évaluer dès le premier tag `v*` amont (`git ls-remote --tags` / tags Docker Hub) ; prérequis alors : postgres 15 + OpenSearch + redis + worker celery, doc d'indexation drive/docs dans le clone `examples/find`.

## Kubernetes : première tranche VALIDÉE (2026-10-24)

- **Cluster kind** (deploy/k8s/kind/kind-config.yaml : ingress sur 8080/8444 — 8443 = compose) + ingress-nginx : livrés.
- **Keycloak 26.8.1 + postgres 18-alpine** en manifests raw, realm rendu par le moteur as-code du CLI (script `deploy/k8s/kind/render-realm.py`, origins `http://*.localhost:8080`, secrets à neuf dans `.runtime/` gitigné — zéro secret committé).
- **Brique Drive via le chart amont** (`values-drive.yaml`, images pinnées v0.25.2), ingress média avec pattern auth-request amont, bucket S3 par Job aws-cli. Smoke curl : OIDC discovery 200, chaîne SSO bout-en-bout avec échange de code in-cluster, `/api/v1.0/items/` 200.
- Reproduction : `bash deploy/k8s/deploy.sh` (idempotent, garde-fou contexte kind). Détails : docs/DEPLOYMENT-K8S.md.
- Limitations : login navigateur bloqué en HTTP pur (Keycloak 26 émet des cookies `Secure` — TLS cert-manager = roadmap) ; secrets en clair dans `.runtime/` (SOPS = roadmap) ; 1 brique validée, les 4 clients OIDC des autres déjà dans le realm.
- **Découverte produit (fix compose)** : l'amont Drive exige `CELERY_BROKER_URL` + un worker celery — absents du compose (tâches async mortes en silence). Corrigé : `drive_celery` + `CELERY_BROKER_URL`, validé live (worker connecté au broker).

## Briques Projets et Agenda LIVRÉES (2026-10-24)

- **projects** (suitenumerique/projects v1.27.12, AGPL-3.0) : monolithe Sails+React
  (port 1337, socket.io — la location / de la passerelle est déjà équipée Upgrade).
  Migrations knex DANS l'entrypoint amont (aucun oneshot). SSO openid-client natif
  (`native_sso = true` : pas d'auto-login passerelle) + `userinfo_plain = true`
  (openid-client v5 veut du JSON ; le PUT Keycloak FUSIONNANT les attributs, la
  désactivation du userinfo signé se fait en posant la valeur à "" et pas en
  omittant la clé). Image amd64 UNIQUEMENT, single-instance imposée (pas de
  REDIS_URL à cette version), tag Hub SANS « v » (piège du typo-tag 1.17.12).
- **calendars** (suitenumerique/calendars v0.1.0, MIT, GHCR) : Django + worker
  dramatiq + SabreDAV (jamais exposé : /.well-known/caldav routé vers le backend
  via le nouveau mécanisme générique `extra_api_locations`) + SPA Caddy. Deux
  schémas en base (Django + `sabre`) : oneshot calendars_caldav_init + migrations
  via le mécanisme générique migrate_service. `DJANGO_SETTINGS_MODULE` requis
  (django-configurations) ; préfixes DJANGO_ALLOWED_HOSTS/DJANGO_CSRF_TRUSTED_ORIGINS.
- 2 clients OIDC provisionnés live dans le realm (flag userinfo conditionnel),
  certificat régénéré avec les nouveaux SAN, smoke 15/15, logins SSO Projects et
  Agenda validés en navigateur (compte demo).
