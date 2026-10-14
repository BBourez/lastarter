# Registre des licences LaStarter

Dernière vérification : lecture directe des fichiers `LICENSE*` / `README` des checkouts
de `examples-inspiration/`. Ce registre est la source de vérité de la **gate licence**
CI (phase 6) : tout changement de régime d'un amont doit y être reporté.

## 1. Résumé exécutif

- **Usage commercial autorisé partout** : aucune brique du catalogue n'interdit
  l'usage commercial.
- Le « non-commercial, ≤100 utilisateurs » rencontré dans l'écosystème ne se trouve
  **que dans le README d'`ess-helm`** (positionnement produit d'Element pour sa
  distribution ESS Community). `ess-helm` est **exclu** du catalogue pour ce motif.
- Les licences libres (MIT, Apache-2.0, AGPL-3.0, GPL-3.0) n'interdisent jamais l'usage
  commercial — c'est une liberté garantie par définition. Ce qui lie LaStarter, ce sont
  des **obligations** (notices, copyleft), pas des interdictions.

## 2. La multilicence Element, clarifiée

`element-web`, `tchap-web-v4` et `element-call` sont **multilicenciés sans condition**.
Le titulaire du copyright (New Vector Ltd / Element) accorde le droit de *choisir* :

1. gratuitement sous **AGPL-3.0** (ou ultérieure), **ou**
2. gratuitement sous **GPL-3.0** (ou ultérieure), **ou**
3. sous **licence commerciale Element payante** (contrat négocié).

Pour un client web servi à des utilisateurs, LaStarter choisit **AGPL-3.0** (voie 1).
La voie 3 existe pour qui ne veut pas assumer le copyleft ou veut une indemnité — ce
n'est pas une obligation pour usage commercial. La licence commerciale d'ESS Pro reste
une **option premium** si un client l'exige explicitement.

Risque résiduel : Element peut changer les conditions des versions *futures* (précédent
en 2024-25). Parade : pins de version + gate licence CI à chaque bump.

## 3. Registre par brique

### Fondation

| Brique | Origine | Licence | Obligations LaStarter |
|---|---|---|---|
| `keycloak` | quay.io/keycloak/keycloak (CNCS) | Apache-2.0 | Notices si redistribution ; branding libre |
| `livekit` (SFU mutualisé) | livekit/livekit-server | Apache-2.0 | idem |

### Apps La Suite numérique (DINUM/ANCT)

| Brique | Origine | Licence | Obligations LaStarter |
|---|---|---|---|
| `drive` | suitenumerique/drive | MIT | Conserver les notices de copyright DINUM ; rebranding obligatoire (pas de nom/logo « La Suite ») |
| `meet` | suitenumerique/meet | MIT | idem |
| `messages` | suitenumerique/messages | MIT | idem |
| `transfers` | ANCT (La Suite territoriale) | MIT | idem |
| `projects` | suitenumerique/projects | AGPL-3.0 | Copyleft : source de la version servie (page SOURCES) ; publier toute modification |

### Chat chiffré (remplace ess-helm)

| Brique | Origine | Licence | Obligations LaStarter |
|---|---|---|---|
| `synapse` | matrixdotorg/synapse | AGPL-3.0 | Copyleft (source de la version servie) |
| `element-web` (**client par défaut** — UX native, recolorée par `custom_themes`/`branding` config, zéro fork) | element-hq/element-web | AGPL-3.0 **ou** GPL-3.0 (au choix) | Version non modifiée = mention source ; si patchs → publier la fourche |
| `tchap-web` (client alternatif — spécificités secteur public FR) | tchapgouv/tchap-web-v4 | AGPL-3.0 **ou** GPL-3.0 (au choix) | idem |
| `element-call` (option) | element-hq/element-call | AGPL-3.0 ou commerciale | Copyleft si modifié ; widget servi non modifié = mention source |
| `lk-jwt-service` | ghcr.io/element-hq/lk-jwt-service | Apache-2.0 | Notices |

### Design system et identité

| Composant | Origine | Licence | Politique LaStarter |
|---|---|---|---|
| Compound (`element-hq/compound`, `compound-design-tokens`) | Element | **AGPL-3.0** (vérifié API GitHub) | **Ne pas construire dessus** nos surfaces propres (portail, login) : code permissif (Radix/shadcn + Tailwind) avec tokens inspirés de l'ergonomie Element — sans copier le code AGPL. Réservé aux overrides de tokens via la config element-web (usage légitif, pas incorporation de code). |

Référence concurrente : LaSuite.coop opère commercialement (cotisations) un chat « basé sur Element » — validation de marché et de viabilité du modèle AGPL pour cette offre.

### Outils de référence (pas livrés aux clients)

| Outil | Origine | Licence | Usage |
|---|---|---|---|
| `st-ansible` / `st-cli` | ANCT | MIT | Modèle d'architecture du CLI (idées, pas copié-collé massif) |

### Exclusions et candidates futures

| Composant | Statut | Motif |
|---|---|---|
| `ess-helm` (ESS Community) | **Exclu** | README : « non-commercial community use cases with up to 100 users » — positionnement Element incompatible avec l'offre B2B. Remplacé par Synapse + element-web assemblés librement. |
| `hub`, `accounts` | Écartés v1 | MIT donc utilisables, mais « Not ready for production yet » — réévaluation phase 5+ (portail custom mince d'abord). |
| Grist (tableur, cf. LaSuite.coop) | Candidate phase 3+ | Vérifier licence à l'ajout effectif (registre à mettre à jour). |

## 4. Conformité opérationnelle

1. **Mentions sources par déploiement** : le CLI génère `deployments/<client>/SOURCES.md`
   listant chaque brique, sa version exacte épinglée, sa licence et l'URL du source
   amont (tag/commit). C'est l'acquittement copyleft pour des versions non modifiées.
2. **Modifications éventuelles** : toute fourche (ex. thème tchap) est publiée dans
   l'organisation LaStarter et référencée dans `SOURCES.md`.
3. **Marques déposées** : « La Suite », « Element », « Tchap »… n'apparaissent dans
   aucune interface livrée aux clients. Le branding est LaStarter ou celui du client
   final. Les notices de copyright (obligatoires) restent dans les fichiers sources et
   la page de mentions.
4. **Gate licence CI** : à chaque bump de pin, scan des `LICENSE*` amont et diff contre
   ce registre ; toute divergence bloque la release et ouvre une tâche de mise à jour
   du registre.
5. **Tchapgouv/tchap-web-v4 précision** : c'est un soft-fork DINUM d'element-web ; le
   régime multilicence (AGPL/GPL/commerciale) est identique à element-web — déclaré tel
   quel dans le README de tchap.
