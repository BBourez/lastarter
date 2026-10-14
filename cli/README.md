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
```

Résultat : `../deployments/<client>/` contenant le manifeste (`lastarter.toml`),
les brouillons d'environnement (`env/*.env`), les secrets générés (`secrets.env`,
gitignoré — à chiffrer), les réponses rejouables (`answers.json`) et les mentions
licences (`SOURCES.md`).

Installation en commande (`pip install -e .` depuis `cli/`) : `lastarter …`.

## Invariants (hérités du modèle st-cli)

1. Les secrets ne sont **jamais re-générés** : créés au premier `init`, repris
   d'`answers.json` ensuite. `secrets.env` n'est jamais réécrit.
2. Un `init` rejoué pré-remplit tout depuis `answers.json` (Entrée = conserver).
3. Rien n'est déployé en phase 1 : `init` ne fait que générer de la configuration
   versionnable. Les effets réseau viendront avec `deploy` (phase 2) derrière ses gates.

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
