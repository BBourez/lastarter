# LaStarter

![CI](https://github.com/BBourez/lastarter/actions/workflows/ci.yml/badge.svg)

**LaStarter est une suite collaborative souveraine, open source, pensée pour
les organisations (B2B)** : messagerie chiffrée, stockage de fichiers,
visioconférence et identité unique — déployées sur VOS serveurs, sous VOTRE
marque, avec un installateur sans aucune dépendance externe.

Le produit n'écrit pas d'application : il assemble des briques open source
éprouvées — l'écosystème **La Suite numérique** et la stack **Matrix** —
**épinglées version par version et jamais modifiées** (aucun patch du code
amont), derrière une couche d'intégration as-code :

- **identité unique** : un realm Keycloak, un SSO OIDC pour toutes les briques ;
- **habillage** : une palette de couleurs pilote le CSS de la passerelle, les
  mécanismes de thématisation natifs de chaque app, les logos et les noms ;
- **déploiement** : docker-compose mono-VM orchestré par une CLI Python
  **zéro dépendance** (stdlib uniquement).

## Briques

| Brique | Rôle | Amont (pin) | Licence |
|---|---|---|---|
| Identité (core) | SSO OIDC, realm as-code | [Keycloak](https://github.com/keycloak/keycloak) 26.3.2 | Apache-2.0 |
| Discussions | Messagerie chiffrée E2EE | [element-web](https://github.com/element-hq/element-web) v1.12.32 + [synapse](https://github.com/element-hq/synapse) v1.163.1 | AGPL-3.0 |
| Drive | Stockage et partage de fichiers | [suitenumerique/drive](https://github.com/suitenumerique/drive) v0.25.2 | MIT |
| Meet | Visioconférence navigateur (SFU LiveKit) | [suitenumerique/meet](https://github.com/suitenumerique/meet) v1.36.2 + [livekit](https://github.com/livekit/livekit) v1.13.6 | MIT / Apache-2.0 |

Registre complet et obligations associées :
[docs/licences.md](docs/licences.md) — vérifiés en CI (`lastarter licenses`).

## Démarrage

Une ligne (bash, docker + python ≥ 3.12 requis) :

```bash
curl -fsSL https://raw.githubusercontent.com/BBourez/lastarter/main/install.sh | bash
```

Ou scripté — client, domaine, briques, puis déploiement :

```bash
curl -fsSL https://raw.githubusercontent.com/BBourez/lastarter/main/install.sh \
  | LASTARTER_CLIENT="ACME" LASTARTER_DOMAIN=acme.example.com \
    LASTARTER_APPS=drive,discussions,meet LASTARTER_DEPLOY=1 bash
```

Variante manuelle :

```bash
git clone https://github.com/BBourez/lastarter && cd lastarter/cli
python -m lastarter_cli init                      # questionnaire interactif
python -m lastarter_cli deploy --client acme --pull
python -m lastarter_cli ps --client acme
```

La CLI est stdlib-only : aucun paquet à installer (`pip install -e .` est
optionnel, pour disposer de la commande `lastarter`). Chaque déploiement vit
dans `deployments/<client>/` : manifeste versionnable (`lastarter.toml`),
brouillons `env/*.env`, coffre de secrets (`secrets.env`, gitigné,
append-only), mentions de licences (`SOURCES.md`), logo (`branding/`).

## Personnalisation (marque blanche)

Tout part du questionnaire `init` — rejouable, pré-rempli, logo conservé :

| Quoi | Comment |
|---|---|
| Palette | `--theme element-light` (ou `element-dark`) — `themes/*.toml` |
| Couleur de marque | `--brand-color "#0bc491"` |
| Logo | `--logo logo.svg` (copié, servi sur `/__lastarter/branding/`) ; défaut : monogramme généré depuis la palette |
| Nom de marque | `--brand "ACME"` |
| Noms des applications | `--app-name-drive "Espace documents"`, `--app-name-meet "Réunions"`, … |

La palette est la source unique : elle produit le `theme.css` de la
passerelle, le mécanisme natif `custom_themes` d'element-web, le JSON de
personnalisation natif du drive et le logo servi par la passerelle. Aucun
fork, aucun patch : uniquement des mécanismes prévus par les amonts.

## Mises à jour

```bash
python -m lastarter_cli check-updates            # veille amont (API GitHub, pré-releases exclues)
python -m lastarter_cli check-updates --strict   # gate : exit 1 si au moins un retard
```

Le workflow hebdomadaire
[`upstream-sync`](.github/workflows/upstream-sync.yml) exécute cette veille et
ouvre une PR listant chaque `pin → nouveau`, à réviser (changelogs, breaking
changes) avant fusion. Rien n'est jamais déployé en `latest` : le tag
`latest` des images La Suite est une preprod.

## Architecture (en 10 lignes)

```
catalogue/*.toml (briques épinglées)        themes/*.toml (palettes)
        │ lastarter init                           │
        ▼                                          ▼
deployments/<client>/ ── lastarter deploy ──▶ .runtime/ (secrets rendus, realm,
(env, secrets, answers, branding)              theme.css, meet/livekit.yaml,
                                               drive/theme-customization.json)
                                                   │
                    docker compose (base + un profil par brique)
                                                   │
  nginx TLS :8443 ◀── id. / chat. / drive. / meet. / livekit.<domaine> + portail (apex)
```

Détails : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ·
opérations : [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Licences et mentions

- Le code LaStarter (catalogue, CLI, compose, docs) : **AGPL-3.0-only**
  ([LICENSE](LICENSE)).
- Les briques amont conservent leurs licences (Apache-2.0, AGPL-3.0, MIT,
  BSD, PostgreSQL License) : registre et obligations dans
  [docs/licences.md](docs/licences.md) — la CI les vérifie à chaque
  changement de catalogue.
- LaStarter n'est ni affilié à, ni approuvé par La Suite numérique
  (DINUM/ANCT), Element ou les éditeurs des composants ; les marques
  « La Suite », « Element », « Tchap » appartiennent à leurs titulaires
  respectifs.

## Feuille de route (honnête)

| Sujet | État |
|---|---|
| compose mono-VM, SSO Keycloak, theming natif, portail | ✅ en service |
| Meet : déployée (images amont, SSO, theming CSS) ; smoke HTTP ; parcours e2e complet (SSO → salon → invitation → appel) à rejouer | ⏳ roadmap |
| Kubernetes (charts amont, external-secrets/SOPS) | ⏳ roadmap |
| Brique documents (lasuite/impress) | ⏳ roadmap |
| MAS (SSO Matrix dédié), TURN/UDP pour meet | ⏳ roadmap |
| Bumps différés : keycloak 26.8.1, postgres 18 | ⏳ roadmap (migration volumes) |

Détails : [docs/ROADMAP.md](docs/ROADMAP.md) · intentions historiques :
[docs/history/](docs/history/).
