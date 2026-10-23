# Architecture LaStarter

## Le modèle : briques amont épinglées + couche d'intégration as-code

Une **brique** = un logiciel libre amont, pris **tel quel**, à une **version
épinglée** (`catalogue/<nom>.toml`), jamais modifié dans son code. Les seules
modifications autorisées d'une brique sont :

1. l'**intégration Keycloak** (SSO OIDC) — exclusivement par configuration et
   variables d'environnement natives de l'amont ;
2. l'**habillage** (couleurs, logos, noms) — exclusivement par les mécanismes
   de thématisation natifs de l'amont (CSS, JSON de personnalisation, config).

Tout le reste — realm, compose, passerelle, portail, thèmes, secrets, veille —
vit dans la couche **as-code** de ce dépôt. Conséquences : une montée de
version = changer un pin (et relire le changelog) ; pas de dette de fork ;
la CI échoue si une licence sort du registre
[docs/licences.md](licences.md).

## Pipeline : catalogue → CLI → déploiement

```
catalogue/*.toml ──(init)──▶ deployments/<client>/
  manifestes TOML              ├─ answers.json      réponses rejouables (marque, briques, noms d'app)
  images + env + secrets       ├─ lastarter.toml    manifeste (pins, licences) — versionnable
  + OIDC + compose             ├─ env/<brique>.env  brouillons committables ({secret:…} non substitués)
                               ├─ secrets.env       coffre réel — gitigné, append-only
                               ├─ branding/logo.*   logo (copié ou monogramme généré)
                               └─ SOURCES.md        mentions licences (offre de source AGPL)

deployments/<client>/ ──(deploy)──▶ <client>/.runtime/
                                     env rendus (secrets substitués), realm Keycloak,
                                     theme.css, branding/, meet/livekit.yaml,
                                     drive/{backend.env, theme-customization.json},
                                     portal/, discussions/, certs/
                                  ▶ docker compose : base.yml + keycloak.yml + <brique>.yml …
                                     infra (healthchecks) → migrations → up -d --wait
```

Invariants du CLI :

- secrets générés une seule fois, coffre **append-only**, jamais committé ;
- `init` rejoué = pré-remplissage intégral, logo existant jamais écrasé ;
- `deploy` passe des gates avant tout effet réseau (docker présent,
  déploiement initialisé, coffre présent, cible compose par brique).

## Topologie de service

```
                      TLS :8443 (EDGE_PORT)
 ┌── nginx passerelle (deploy/compose/keycloak.yml) ◀── certs (.runtime/certs ; POC = CA locale)
 │    *.domaine : id. (Keycloak) · apex (portail statique) · chat. / drive. / meet. / livekit.
 │    /__lastarter/theme.css · /__lastarter/fonts/ · /__lastarter/auto-login.js · /__lastarter/branding/
 ▼
 keycloak (realm lastarter) ← clients OIDC : synapse, drive, meet
 discussions_synapse + discussions_element_web        (API Matrix same-origin : /_matrix, /_synapse)
 drive_backend + drive_frontend + postgres + redis + rustfs   (API Django same-origin : /api, /admin, /static)
 meet_backend + meet_frontend + postgres + redis + rustfs + meet_livekit   (SFU : livekit.<domaine>, websocket)
```

Chaque brique expose son frontend via la passerelle et sert ses API en
same-origin (un sous-domaine par brique : pas de CORS, cookies dédiés). Les
clients OIDC du realm déclarent des redirectUris `{origin}/*` : tout callback
d'une brique est couvert sans chemin exact à déclarer.

## Flux SSO Keycloak

1. `identity/realm-lastarter.json` (realm, utilisateur de démo, clients) est
   importé au premier démarrage (`--import-realm`) ; ensuite l'API admin fait
   autorité — provisionnement idempotent : les secrets des clients OIDC sont
   resynchronisés au `deploy` suivant si le coffre change.
2. Une app non authentifiée redirige vers `id.<domaine>` (realm
   `lastarter`) ; la page de login est brandée (thème Keycloak as-code).
3. Les apps « auto-login » reçoivent `/__lastarter/auto-login.js` injecté par
   la passerelle (`auth_url=/api/v1.0/authenticate/` côté django-lasuite) ;
   les discussions (element/synapse) ont leur chemin OIDC natif et sont
   exclues de cette injection.
4. Déconnexion : endpoints OIDC natifs de chaque amont (`OIDC_OP_LOGOUT_*`).

## Chaîne d'habillage (theming)

Une seule source : `themes/<nom>.toml` (palette : canvas, polices, échelles
primary/neutral/statuts, composants), rendue par le CLI contre le gabarit
`identity/theme.css.tpl` :

| Cible | Mécanisme | Sortie |
|---|---|---|
| Passerelle + apps Django/Cunningham | `theme.css` servi sur `/__lastarter/theme.css`, injecté via `sub_filter </head>` | `.runtime/theme.css` |
| element-web (discussions) | mécanisme NATIF `custom_themes` : clés `--cpd-color-*` **scannées dans le même gabarit** + `default_theme: custom-<nom>` | `config.json` re-dumpé |
| drive (La Suite) | NATIF : `THEME_CUSTOMIZATION_FILE_PATH` (JSON footer : liens, licence, logo) + `FRONTEND_THEME` (dsfr-light/dsfr-dark) + `FRONTEND_CSS_URL` | `.runtime/drive/theme-customization.json` |
| meet (La Suite) | NATIF : `FRONTEND_CUSTOM_CSS_URL` → `/__lastarter/theme.css` | env rendu |
| Logo + noms | branding servi sur `/__lastarter/branding/`, noms d'app dans les tuiles du portail | `.runtime/branding/`, `answers.json` (apps) |

Les 13 `sub_filter` historiques aux couleurs codées en dur ont été
supprimés : toutes les apps disposent désormais d'un mécanisme CSS natif.

## Veille amont et montées de version

- `check-updates` compare chaque pin (`upstream_repo` + `upstream_pin`) aux
  tags/releases GitHub, pré-releases exclues (le `latest` lasuite est une
  preprod). synapse et livekit n'ont pas de champ propre : suivi manuel.
- Workflow hebdomadaire `upstream-sync` : met à jour les pins en retard et
  ouvre une PR de revue (changelogs + breaking changes).
- Montée de version : modifier le pin (et les images `[env]` concernées) du
  catalogue → `deploy --client X --pull`. Postgres en version majeure =
  migration de volume (pg_dump/restore) — voir [DEPLOYMENT.md](DEPLOYMENT.md).

## Qualité

- CLI **zéro dépendance** (Python ≥ 3.12, `tomllib`) : tests offline
  (`python -m unittest discover -s tests` depuis `cli/`), verts en CI sur
  Python 3.12 et 3.13.
- Gates `deploy` (docker, déploiement initialisé, coffre, cible compose) et
  `licenses` (registre [licences.md](licences.md)) avant tout effet.
- CI : tests CLI, catalogue + licences, rendu `init` non interactif avec
  asserts — aucun docker requis.

## Arborescence

```
lastarter/
├── catalogue/      manifestes TOML par brique (SCHEMA.md)
├── cli/            lastarter-cli (Python stdlib) + tests unittest
├── deploy/
│   ├── compose/    base.yml + keycloak.yml (passerelle/SSO) + <brique>.yml
│   └── k8s/        cible Kubernetes (roadmap — README)
├── identity/       realm Keycloak as-code + gabarits (theme.css.tpl, configs apps)
├── portal/         portail statique (apex)
├── themes/         palettes (*.toml)
├── scripts/e2e/    parcours navigateur (playwright-core, canal Edge)
├── docs/           documentation (+ history/, licences.md, roadmap)
└── deployments/    arbres générés par le CLI (un dossier par client)
```
