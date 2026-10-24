# libs/compound — jetons Compound vendus (copie canonique)

Copie **verbatim** des fichiers de jetons générés par
[`@element-hq/compound-design-tokens`](https://github.com/element-hq/compound-design-tokens)
(dépôt officiel du design system **Compound** d'Element, licence Apache-2.0).
Aucune règle n'est réécrite : ce sont les fichiers amont, recopiés tels quels.

## Contenu

| Fichier | Rôle |
|---|---|
| `cpd-common-base.css` | jetons d'espacement, rayons, typographie (`--cpd-space-*`, `--cpd-radius-*`) |
| `cpd-common-semantic.css` | jetons sémantiques (`--cpd-color-text-*`, `--cpd-color-bg-*`, bordures) |
| `cpd-theme-light-base-mq.css` | palette claire complète (`--cpd-color-gray-*`, accents) via media-query |
| `cpd-font-fallbacks.css` | piles de polices de repli |

## Consommateurs

- **Thème Keycloak** (`identity/keycloak-theme/lastarter/login/resources/css/`) :
  copies embarquées dans le thème (servi in-conteneur) — même contenu, même source.
- **Habillage des apps** (`identity/theme.css.tpl`) : le pont Cunningham
  (`--c--*` → palette de `themes/*.toml`) dérive de ces jetons ; les apps
  La Suite (docs/drive/meet) consomment ces variables **nativement** via
  Cunningham — aucune règle structurelle n'est injectée (bug « boutons
  doublés » corrigé à ce titre).
- **Portail** (`portal/portal.css`) : mêmes jetons via les variables
  `--cpd-*` rendues par la passerelle.

## Rafraîchissement

1. `npm pack @element-hq/compound-design-tokens` (ou récupérer l'archive du
   release GitHub amont) ;
2. remplacer les fichiers `cpd-*.css` ici ET dans le thème Keycloak (copies
   embarquées) ;
3. vérifier le diff des variables contre `identity/theme.css.tpl` (le pont
   `--c--*` doit rester aligné sur l'échelle amont) ;
4. vérifier visuellement : portail, login Keycloak, docs, drive, meet.

> Discussions (Element Web) n'a pas besoin de cette librairie : il consomme
> Compound nativement.
