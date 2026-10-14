# lastarter-cli

Installateur modulaire de la suite LaStarter. **Zéro dépendance** (Python ≥ 3.12,
stdlib uniquement, TOML via `tomllib`).

## Utilisation

Depuis ce dossier (`cli/`) :

```bash
python -m lastarter_cli list                 # briques du catalogue + dépendances
python -m lastarter_cli init                 # questionnaire interactif
python -m lastarter_cli init --non-interactive \
    --client "ACME" --domain acme.example.com --bricks drive
python -m lastarter_cli deploy --client acme --pull   # gates → infra → migrate → up --wait
python -m lastarter_cli ps --client acme               # état des conteneurs
python -m lastarter_cli deploy --client acme --down    # arrêt (volumes conservés)
```

Résultat de `init` : `../deployments/<client>/` contenant le manifeste (`lastarter.toml`),
les brouillons d'environnement (`env/*.env`), les réponses rejouables (`answers.json`)
et les mentions licences (`SOURCES.md`). `deploy` rend `.runtime/` (env avec secrets
substitués + realm Keycloak) — **gitignoré** — puis orchestre compose.

Installation en commande (`pip install -e .` depuis `cli/`) : `lastarter …`.

## Invariants (hérités du modèle st-cli)

1. Les secrets ne sont **jamais re-générés** : créés au premier `init`, repris de
   `secrets.env` ensuite ; le coffre croît en *append-only* (les nouveaux secrets
   du catalogue sont ajoutés, jamais les valeurs existantes modifiées).
2. Un `init` rejoué pré-remplit tout depuis `answers.json` (Entrée = conserver).
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
