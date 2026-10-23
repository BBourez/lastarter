# Registre des licences — LaStarter

LaStarter n'écrit pas d'application : il assemble des logiciels libres
**épinglés et non modifiés** (aucun patch du code amont) derrière une couche
d'intégration as-code (realm Keycloak, compose, passerelle, habillage par
variables d'environnement). Le code LaStarter lui-même est distribué sous
**AGPL-3.0-only** (voir [`LICENSE`](../LICENSE) à la racine du dépôt).

Ce registre est la source de vérité juridique du dépôt. La commande
`lastarter licenses` — et le job `catalogue` de la CI — vérifie que chaque
brique du catalogue porte une licence de liste blanche **et** figure
ci-dessous ; toute divergence casse la CI volontairement.

## Briques du catalogue

| Brique (`catalogue/<nom>.toml`) | Amont | Version épinglée | Licence |
|---|---|---|---|
| `keycloak` | [keycloak/keycloak](https://github.com/keycloak/keycloak) — image `quay.io/keycloak/keycloak` | 26.3.2 | Apache-2.0 |
| `discussions` (client web) | [element-hq/element-web](https://github.com/element-hq/element-web) — image `ghcr.io/element-hq/element-web` | v1.12.32 | AGPL-3.0 OR GPL-3.0 OR Element-Commercial — **LaStarter choisit AGPL-3.0** |
| `discussions` (homeserver Matrix) | [element-hq/synapse](https://github.com/element-hq/synapse) — image `matrixdotorg/synapse` | v1.163.1 | AGPL-3.0-only |
| `drive` (backend + frontend) | [suitenumerique/drive](https://github.com/suitenumerique/drive) — images `lasuite/drive-backend` + `lasuite/drive-frontend` | v0.25.2 | MIT |
| `meet` (backend + frontend) | [suitenumerique/meet](https://github.com/suitenumerique/meet) — images `lasuite/meet-backend` + `lasuite/meet-frontend` | v1.36.2 | MIT |
| `meet` (SFU audio/vidéo) | [livekit/livekit](https://github.com/livekit/livekit) — image `livekit/livekit-server` | v1.13.6 | Apache-2.0 |

## Composants d'infrastructure (compose, hors catalogue)

| Composant | Image | Version | Licence |
|---|---|---|---|
| PostgreSQL (base identité Keycloak) | `postgres` | 14.3 | PostgreSQL License (permissive) |
| PostgreSQL (bases drive et meet) | `postgres` | 16 | PostgreSQL License (permissive) |
| Redis (cache/broker drive et meet) | `redis` | 5 | BSD-3-Clause (le dual licensing RSAL/SSPL n'intervient qu'à partir de Redis 7.4) |
| Passerelle TLS (edge) | `nginx` | 1.25-alpine | BSD-2-Clause |
| Stockage objet compatible S3 | `rustfs/rustfs` | 1.0.3 | Apache-2.0 |
| Initialisation des buckets (conteneurs one-off `createbuckets`) | `amazon/aws-cli` | suit le compose amont | Apache-2.0 |

## Obligations par régime de licence

### AGPL-3.0 — element-web, synapse, et le code LaStarter lui-même

- **Offre de source** : les briques sont servies sur un réseau ; l'AGPL-3.0
  (§13) impose de proposer le code source correspondant aux utilisateurs.
  Couverture : chaque déploiement génère `SOURCES.md` (table
  brique / licence / version épinglée / dépôt amont), et le dépôt public
  LaStarter publie l'intégralité de la couche d'intégration.
- **Versions identifiables** : les pins de `catalogue/` désignent la version
  exacte servie ; les sources amont sont celles des repos ci-dessus à ces tags.
- **Notices** : conserver les mentions de copyright et de licence (incluses
  aux images amont, jamais retirées).
- **Modifications** : aucune modification du code amont (règle produit) ;
  si cela changeait un jour, les sources modifiées devraient être publiées
  sous AGPL-3.0 et référencées dans `SOURCES.md`.

### Apache-2.0 — keycloak, livekit, rustfs, aws-cli

- Conserver le fichier `LICENSE` et les notices `NOTICE` (inclus aux images
  amont) ; indiquer les modifications éventuelles (aucune) ; ne pas utiliser
  les marques des projets pour promouvoir un produit dérivé.

### MIT — drive, meet (La Suite numérique)

- Conserver la notice de copyright et le texte d'autorisation dans toutes les
  copies ou parties substantielles — garanti par la conservation des fichiers
  LICENSE/COPYRIGHT des images amont et par les mentions de `SOURCES.md`.

### BSD-2-Clause / BSD-3-Clause / PostgreSQL License — nginx, redis, postgres

- Redistribuer la notice de copyright amont (incluses aux images) ;
  BSD-3-Clause : ne pas utiliser les noms des projets à des fins de promotion
  sans permission écrite préalable.

## Marques

- **Element** est une marque d'Element Software / New Vector Ltd ; **Tchap**
  est un service et une marque de la DINUM (État français).
- **La Suite numérique** (et la marque « La Suite ») est un programme de
  l'État français (DINUM / ANCT) ; « LaStarter » est un projet indépendant.
- LiveKit, Keycloak, Redis, nginx, PostgreSQL, RustFS : marques de leurs
  titulaires respectifs.

LaStarter n'est **ni affilié à, ni approuvé par** ces éditeurs. Les marques ne
sont pas utilisées dans les interfaces livrées aux clients : l'habillage
(logo, couleurs, noms d'applications) provient du branding LaStarter ou du
client final (personnalisé via `lastarter init`).

## Procédure de changement de régime

Nouvelle brique, ou changement de licence d'un amont : mettre à jour ce
registre (revue juridique) **puis** la liste blanche `ALLOWED_LICENSES` de
`cli/lastarter_cli/cmd/licenses.py`. Dans l'ordre inverse, la CI échoue —
c'est voulu : le registre prime sur le code.
