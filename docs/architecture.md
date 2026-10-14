# Architecture LaStarter

## 1. Modèle : distribution, pas fusion

LaStarter est un repo *umbrella* qui orchestre des applications amont **non forkées**,
consommées comme des versions épinglées (images Docker / refs Git / charts). C'est le
modèle « éditeur de distribution » (Element avec ESS, Canonical avec Ubuntu, Bitnami).

Pourquoi pas une fusion en un seul logiciel :

- 7+ dépôts amont très actifs (Meet est déployé à toute la fonction publique française) :
  une fusion = fork permanent, conflits à chaque mise à jour, retard sur les correctifs
  de sécurité.
- Stacks hétérogènes (Django, Next.js, React/Vite, Rust) : une équipe ne peut pas tout
  maîtriser ; l'amont oui.
- La valeur vendue n'est pas le code des apps : c'est la **sélection**, l'**intégration
  SSO**, la **marque blanche**, l'**installation sur mesure**, les **mises à jour
  maîtrisées** et le **support**.

L'intégration se fait exclusivement dans la couche orchestration :

```
                    ┌─────────────────────────────────────────────┐
                    │                lastarter-cli                │
                    │  init · deploy · ps · logs · add · remove   │
                    │  upgrade · doctor                            │
                    └───────────────┬─────────────────────────────┘
                                    │ génère / pilote
        ┌───────────────────────────┼───────────────────────────────┐
        ▼                           ▼                               ▼
 deployments/<client>/      deploy/compose | k8s        identity/ (realm Keycloak)
 manifeste versionné Git    profils par brique           clients OIDC auto-provisionnés
 secrets chiffrés           docker-compose ou Helm       au déploiement
        │                           │                               │
        └───────────────────────────┼───────────────────────────────┘
                                    ▼
                     ┌────────────────────────────┐
                     │  Keycloak (identité unique)│◄──── SSO pour toutes les briques
                     └────────────┬───────────────┘
        ┌──────────────┬──────────┼──────────────┬──────────────┐
        ▼              ▼          ▼              ▼              ▼
     Drive           Meet      Messages      Transfers     Chat (Synapse
   (fichiers)      (visio)     (mail)      (transfert)   + Tchap + element-call)
        │              │                                      │
        └── RustFS/S3 ─┘            └──────── LiveKit mutualisé ───────┘
                                     (SFU partagé meet / appels chat)
                                    ▼
                              Portail SSO (point d'entrée unique)
```

## 2. Briques et dépendances

Chaque brique est décrite dans `catalogue/<nom>.toml` : version épinglée, licence,
dépendances envers d'autres briques, variables de branding, variables d'environnement
principales, services compose.

Dépendances inter-briques (phase 1) :

- `keycloak` — **fondation**, toujours installée (SSO de toutes les briques).
- `drive` — requiert `keycloak` (OIDC). Ses dépendances *internes* (postgresql, redis,
  RustFS/S3, collabora/onlyoffice, nginx) font partie de son profil compose et ne sont
  pas des briques séparées.

Phases suivantes : `meet` (+ LiveKit partagé), `messages`, `transfers`, `projects`,
`synapse` + `tchap-web` (+ `element-call` en option), chacun avec `requires = ["keycloak"]`.

Le CLI résout automatiquement les dépendances : sélectionner `drive` ajoute `keycloak`
si absent (avec notification), comme `st-cli` le fait pour meet → livekit.

## 3. Le CLI (`lastarter-cli`)

Modèle sur `st-cli` (suitenumerique/st-ansible, MIT) dont l'architecture est éprouvée :
questionnaire → arbre de config versionné → déploiement → upgrades rejouables.

| Commande | Rôle |
|---|---|
| `list` | Lister les briques du catalogue |
| `init` | Questionnaire client (briques, domaine, branding) → `deployments/<client>/` |
| `deploy` | (phase 2+) Générer/exécuter compose ou Helm avec les secrets |
| `ps` / `logs` | (phase 2+) État et journaux du déploiement client |
| `add` / `remove` | Activer / retirer une brique chez un client existant |
| `upgrade` | (phase 3+) Bump de pins + rejeu pré-rempli du questionnaire + étapes manuelles |
| `doctor` | (phase 3+) Dérive entre catalogue et arbre commité |

Invariants repris de st-cli :

- Les secrets ne sont **jamais re-générés silencieusement** : générés à l'`init` s'ils
  n'existent pas, sinon conservés tels quels.
- Un `init` rejoué sur un déploiement existant pré-remplit toutes les réponses depuis
  `answers.json` (rejeu « Enter-through » = arbre identique).
- Les actions à effet de bord réseau (`deploy`) sont bloquées par des gates de cohérence
  (pins, secrets présents) avant toute exécution.

Contrainte d'implémentation : **zéro dépendance Python** (stdlib uniquement, TOML via
`tomllib`), pour un outil installable partout sans friction. Phase 3 : évaluer
Typer/questionary si l'ergonomie interactive le justifie.

## 4. Identité : Keycloak as-code

- Un realm `lastarter` par déploiement client, importé au démarrage
  (`--import-realm`) puis piloté par l'API admin pour les clients OIDC des briques
  activées (mot de passe/secret partagés via env).
- Chaque brique déclare son client OIDC (`client_id`, scopes, redirects) dans son
  manifeste — le CLI transmet ces valeurs au provisionnement.
- Le realm de dev de drive (`docker/auth/realm.json` amont) sert de gabarit (phase 2).

## 5. Branding marque blanche — stratégie 80/20

Objectif : une « vraie identité graphique LaStarter » sans diverger des upstreams.
Positionnement (décision actée, cf. analyse LaSuite.coop et licences) :

| Surface | Identité | Moyen |
|---|---|---|
| Chat | UX Element native, couleurs LaStarter | `element-web` + `custom_themes` / `branding.*` config (docs/theming.md amont) — **zéro fork** |
| Portail, login Keycloak, emails | Identité forte LaStarter | Nos surfaces : base **permissive** (Radix/shadcn + Tailwind), ergonomie inspirée d'Element |
| Drive, Meet, Messages, Transfers | Cohérence (palette + logos) | Variables de branding white-label de chaque app (`FRONTEND_THEME`, `DJANGO_EMAIL_BRAND_NAME`, …) |
| Reskin Compound d'une app | Exception assumée | Uniquement si le business le justifie → fork publié (AGPL), jamais par défaut |

Règles :

- **Compound (design system Element) est AGPL-3.0** : ne pas incorporer son code dans nos
  surfaces propres ; s'en inspirer ergonomiquement, ou l'overrider via la config
  element-web (`compound` dans `custom_themes`).
- Zéro patch de code tant que le branding par config suffit ; si un patch devient
  inévitable (ex. thème tchap), la fourche est publiée (obligation copyleft — voir
  docs/licences.md).
- `branding/<client>.toml` surcharge les valeurs par défaut du catalogue.

## 6. Déploiement

- **Mono-VM (phase 2)** : `deploy/compose/` — un docker-compose de base + profils par
  brique (`docker compose --profile drive,meet up`), réseau partagé unique (modèle
  `lasuite-network` observé dans les compose amont), secrets via fichiers env générés.
- **Kubernetes (phase 5)** : Helm umbrella consommant les charts amont (meet en publie
  un officiel) + charts communautaires éprouvés pour les briques sans chart.

## 7. Mises à jour et qualité (phase 6)

- Renovate sur les pins du catalogue → PR de bump par brique.
- Gate licence en CI : liste blanche MIT / Apache-2.0 / AGPL-3.0 / GPL-3.0 ; toute
  anomalie (changement de régime d'un amont) bloque la release.
- Smoke tests e2e par release : chaque brique démarre, répond à son healthcheck,
  authentifie via Keycloak.
- SBOM + `SOURCES.md` généré par déploiement (conformité copyleft).
