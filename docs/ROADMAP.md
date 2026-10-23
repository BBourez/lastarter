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
