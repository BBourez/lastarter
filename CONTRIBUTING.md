# Contribuer à LaStarter

## Prérequis

- Python >= 3.12 — la CLI est **stdlib-only**, rien à installer ;
- Docker avec plugin compose (optionnel en dev — requis pour `deploy`, `smoke`
  et les vérifications `docker compose config`) ;
- bash (Linux, macOS ou WSL2 ; Git Bash sous Windows).

## Installation

```bash
git clone https://github.com/BBourez/lastarter.git
cd lastarter
# Aucune dépendance à installer. Optionnel, pour disposer de la commande `lastarter` :
cd cli && pip install -e .
```

## Développement

Depuis la racine du dépôt :

```bash
# Tests unitaires (offline, zéro dépendance)
cd cli && python -m unittest discover -s tests

# Catalogue + gate licences (le registre docs/licences.md doit rester conforme)
PYTHONPATH=cli python -m lastarter_cli list
PYTHONPATH=cli python -m lastarter_cli licenses

# Veille amont (API GitHub ; --strict = exit 1 si un pin décroche)
PYTHONPATH=cli python -m lastarter_cli check-updates

# Rendu d'un client de test (aucun docker requis)
PYTHONPATH=cli python -m lastarter_cli init --client acme --domain acme.example.com \
  --bricks drive,discussions,meet --theme element-light --non-interactive

# SBOM CycloneDX d'un déploiement
PYTHONPATH=cli python -m lastarter_cli sbom --client acme
```

## Bonnes pratiques

### Zéro dépendance

La CLI ne dépend que de la bibliothèque standard : pas de `requirements.txt`,
pas de lockfile Python. Toute nouvelle fonctionnalité reste dans ce cadre
(`urllib` pour le réseau, `tomllib`/`json`/`re`/`hashlib` pour le reste).

### Briques amont intouchées

Aucun patch du code amont : une brique s'intègre uniquement par configuration
 natives (variables d'environnement, realm OIDC, mécanismes de thématisation
natifs) et reste épinglée (`catalogue/<nom>.toml`). Voir
[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

### Secrets

Les brouillons `env/*.env` ne contiennent que des jetons `{secret:…}` ; les
valeurs réelles vivent dans `deployments/<client>/secrets.env` (gitigné,
append-only). Ne jamais committer un secret en clair.

### Encodage

Tous les fichiers texte sont en UTF-8 ; les rendus de la CLI écrivent en
UTF-8 explicite.

### Commits

Format : `type : description courte`

Types : `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

## CI

La CI GitHub Actions (`.github/workflows/ci.yml`) vérifie, tous bloquants :

1. **cli-tests** : `unittest discover` offline (Python 3.12 et 3.13) ;
2. **catalogue** : `list` + gate `licenses` (liste blanche + docs/licences.md) ;
3. **rendu** : `init` non interactif d'un client temporaire avec assertions.

La veille amont (`.github/workflows/upstream-sync.yml`) tourne chaque semaine :
`check-updates` compare les pins du catalogue aux derniers tags amont et ouvre
une PR de revue (changelogs / breaking changes) avant toute fusion.

## Signaler un bug

Ouvrir une issue avec : description, étapes de reproduction, comportement
attendu vs observé, et la sortie de `python -m lastarter_cli detect`.
