# LaStarter — Suite numérique B2B « marque blanche »

**LaStarter** est une *distribution* : une suite de services numériques professionnels
(drive, visio, chat chiffré, mail, transfert de fichiers…) assemblée, intégrée et
maintenue sous une seule marque, installable à la carte chez chaque client B2B.

## Principes

1. **Distribution, pas fusion.** Les applications (drive, meet, tchap…) sont consommées
   **non modifiées** depuis leurs dépôts amont, épinglées par version. Les mises à jour
   amont (correctifs de sécurité inclus) continuent d'affluer gratuitement.
2. **L'intégration vit dans la couche orchestration** : identité unique (Keycloak/OIDC),
   portail SSO, branding par variables d'environnement, déploiement modulaire.
   Jamais dans le code des applications.
3. **Installateur à la carte.** `lastarter-cli` pose un questionnaire (quelles briques
   pour ce client ? quel domaine ? quel thème ?) et génère un arbre de configuration
   versionné Git, prêt à déployer en docker-compose (mono-VM) ou Kubernetes.
4. **Conformité licences outillée.** Chaque déploiement embarque une page de mentions
   sources (`SOURCES.md`) ; la CI contrôle les licences à chaque bump de version.

## Structure du dépôt

```
lastarter/
├── catalogue/     Briques épinglées (manifestes TOML : version, deps, branding, env)
├── cli/           lastarter-cli (Python 3.12+, zéro dépendance) — init / deploy / …
├── deploy/        compose/ (profils docker-compose mono-VM) et k8s/ (Helm umbrella)
├── identity/      Realm Keycloak as-code : clients OIDC de chaque brique
├── branding/      Thèmes clients (logos, couleurs) injectés par variables d'env
├── portal/        Portail SSO d'entrée unique (launchpad + annuaire des briques)
├── ci/            Renovate (pins), smoke tests, SBOM, gate licence, releases
├── docs/          Architecture, registre des licences
└── deployments/   Arbres de configuration générés par le CLI (un dossier par client)
```

## Démarrage rapide (maquette phase 1)

```bash
cd cli
python -m lastarter_cli list                 # lister les briques du catalogue
python -m lastarter_cli init                 # questionnaire interactif
# variante scriptable :
python -m lastarter_cli init --client "ACME" --domain acme.example.com \
    --bricks keycloak,drive --non-interactive --output ../deployments
```

Le résultat est un dossier `deployments/acme/` contenant le manifeste client, les
brouillons d'environnement, les secrets générés (à chiffrer) et les mentions sources.

## Feuille de route

| Phase | Contenu | Statut |
|---|---|---|
| 1 | Fondations : scaffold, catalogue (keycloak, drive), maquette CLI `init` | ✅ |
| 2 | POC vertical : compose keycloak+drive, realm as-code, branding | ⏳ |
| 3 | CLI v1 + catalogue étendu (meet, messages, transfers) | |
| 4 | Chat : synapse + OIDC Keycloak + tchap-web, puis element-call | |
| 5 | Portail SSO + Helm umbrella (k8s) | |
| 6 | Industrialisation : Renovate, smoke tests, SBOM, gate licence | |

## Origine des briques et licences

LaStarter assemble des logiciels libres, principalement l'écosystème
**La Suite numérique** (DINUM/ANCT, licence MIT) et la stack **Matrix** (Synapse AGPL-3.0,
Tchap AGPL-3.0/GPL-3.0 au choix, LiveKit Apache-2.0). Voir
[docs/licences.md](docs/licences.md) — le registre complet et les obligations associées.

LaStarter n'est ni affilié ni endorsement par ces éditeurs ; les marques « La Suite »,
« Element », etc. appartiennent à leurs titulaires respectifs et ne sont pas utilisées
dans l'interface livrée aux clients (branding LaStarter ou du client final).
