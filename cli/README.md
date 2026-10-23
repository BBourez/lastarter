# lastarter-cli

Installateur modulaire de la suite LaStarter. **Zéro dépendance** (Python ≥ 3.12,
stdlib uniquement, TOML via `tomllib`).

## Utilisation

Depuis ce dossier (`cli/`) :

```bash
python -m lastarter_cli list                 # briques du catalogue + dépendances
python -m lastarter_cli init                 # questionnaire interactif
python -m lastarter_cli init --non-interactive \
    --client "ACME" --domain acme.example.com --bricks drive,meet \
    --theme element-light --brand-color "#0bc491" \
    --logo ./acme.svg --app-name-drive "Espace documents" --app-name-meet "Réunions"
python -m lastarter_cli deploy --client acme --pull   # gates → infra → migrate → up --wait
python -m lastarter_cli ps --client acme               # état des conteneurs
python -m lastarter_cli deploy --client acme --down    # arrêt (volumes conservés)
```

### Options d'`init` (interactif et `--non-interactive`)

| Option | Rôle |
|---|---|
| `--theme <nom>` | Palette `themes/<nom>.toml` — une palette pilote TOUT l'habillage |
| `--brand-color <hex>` | Couleur de marque du CSS (la palette reste la base) |
| `--logo <fichier>` | Logo `.svg`/`.png`, copié dans `deployments/<client>/branding/` ; défaut : monogramme SVG généré (1re lettre du nom de marque, couleur primaire de la palette) |
| `--logo-url <url>` | URL de logo explicite (prioritaire sur le branding servi) |
| `--app-name-<brique>` | Nom d'affichage de la brique (tuiles du portail, personnalisation apps) ; dérivé du catalogue |

Résultat de `init` : `../deployments/<client>/` contenant le manifeste
(`lastarter.toml`), les brouillons d'environnement (`env/*.env`), le logo
(`branding/`), les réponses rejouables (`answers.json`, structure
`{"brand": {"name", "logo_path"}, "apps": {"<brique>": {"label"}}}` — miroirs
rétro-compatibles `brand_name`/`logo_url` conservés) et les mentions licences
(`SOURCES.md`). `deploy` rend `.runtime/` (env avec secrets substitués, realm
Keycloak, thème, branding) — **gitignoré** — puis orchestre compose.

Installation en commande (`pip install -e .` depuis `cli/`) : `lastarter …`.

## Habillage : une palette → toutes les cibles (zéro patch code amont)

Au déploiement, depuis `themes/<nom>.toml`, le CLI génère :

1. **`theme.css`** (gabarit `identity/theme.css.tpl`) — servi par la passerelle
   sur `/__lastarter/theme.css`, injecté dans le HTML des apps Django/Cunningham
   (`sub_filter` `</head>`) ;
2. **Element Web (discussions)** — mécanisme NATIF amont (docs/theming.md) :
   `setting_defaults.custom_themes = [{name, is_dark, compound}]` avec clés
   `--cpd-color-*` dérivées du MÊME gabarit que le CSS (une seule source de
   vérité) + `default_theme: "custom-<nom>"` ;
3. **Drive** — JSON natif `THEME_CUSTOMIZATION_FILE_PATH` (docs/customization.md
   amont) rendu en `.runtime/drive/theme-customization.json` : structure
   `{"footer": {"default", "fr"}}` aux clés `FooterProps`
   (`externalLinks`, `legalLinks`, `license`, `logo`) ; `FRONTEND_THEME` suit
   light/dark de la palette (`dsfr-light` / `dsfr-dark`) ;
4. **Branding** — `deployments/<client>/branding/` copié vers
   `.runtime/branding/` et servi par la passerelle sur `/__lastarter/branding/`
   (tous les sous-domaines) ; les fonts et l'auto-login restent sur
   `/__lastarter/fonts/` et `/__lastarter/auto-login.js`.

Les anciens `sub_filter` nginx aux couleurs codées en dur sont supprimés : les
apps La Suite ont désormais toutes un mécanisme CSS natif.

## Veille amont : `check-updates`

```bash
python -m lastarter_cli check-updates            # rapport lisible
python -m lastarter_cli check-updates --json     # [{brique, pin, latest, a_jour}, …]
python -m lastarter_cli check-updates --strict   # exit 1 si au moins un retard (gate CI de veille)
```

Interroge l'API GitHub via `urllib` (zéro dépendance) : `/tags` pour
suitenumerique (pas de releases amont ; le « latest » lasuite étant une
preprod, les tags `-pre`, `-preprod`, `-rcN` sont exclus), `/releases` pour
element-hq. Comparaison sémantique (mini-parseur semver stdlib). La commande
**n'écrit rien** : elle est la source du workflow CI de veille. Fetcher
injectable pour les tests offline : `check_updates(bricks, fetcher=…)`.

## Qualité et conformité

```bash
python -m lastarter_cli licenses                 # gate : toute brique doit être dans la liste blanche (docs/licences.md)
python -m lastarter_cli smoke --client acme      # surfaces HTTP (portail, SSO, apps) avec la CA du déploiement
python -m lastarter_cli sbom --client acme       # inventaire CycloneDX des briques épinglées
python -m lastarter_cli detect [--domain …]      # audit environnement (Docker, ports, DNS, IP)
```

## Invariants (hérités du modèle st-cli)

1. Les secrets ne sont **jamais re-générés** : créés au premier `init`, repris de
   `secrets.env` ensuite ; le coffre croît en *append-only* (les nouveaux secrets
   du catalogue sont ajoutés, jamais les valeurs existantes modifiées).
2. Un `init` rejoué pré-remplit tout depuis `answers.json` (Entrée = conserver) ;
   le logo existant (`branding/`) est conservé, jamais écrasé.
3. `deploy` passe des gates avant tout effet réseau : docker présent, déploiement
   initialisé, coffre présent, chaque brique a une cible compose. Les secrets ne
   quittent jamais `deployments/<client>/.runtime/` (gitignoré).
4. Orchestration en 3 temps : infra (healthchecks verts) → migrations one-off →
   pile complète (`up -d --wait`).

## Tests

```bash
python -m unittest discover -s tests -v
```

## Ajouter une brique au catalogue (checklist)

1. Créer `../catalogue/<nom>.toml` conforme au schéma (`../catalogue/SCHEMA.md`).
2. `maturity = "planned"` tant qu'elle n'est pas déployable, `"stable"` ensuite.
3. Déclarer `requires` (briques seulement — postgres/redis/etc. sont internes).
4. Référencer la licence dans `../docs/licences.md` (gate licence CI).
5. `python -m unittest discover -s tests` doit rester vert.
