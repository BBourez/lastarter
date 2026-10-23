# Tests E2E LaStarter (navigateur réel, Edge headless via playwright-core)

Volonté produit : **tout tester à chaque fois**. Ces scripts rejouent les
parcours client complets contre un déploiement actif (POC compris).

État : deux scripts actifs — `element-web.js` (chat) et `meet.js` (visio
suitenumerique : SSO → création → invitation → jonction 2 participants).
Le parcours meet est **implémenté** ; au 2026-10-23 il est bloqué côté
**déploiement** (bug produit, cf. bloc dédié plus bas), pas côté script.

## Prérequis

```bash
npm i            # dans ce dossier (package.json autoportant : playwright-core)
# Edge est utilisé via channel:msedge (aucun téléchargement de navigateur)
# La CA du déploiement doit être dans le magasin Windows (import .runtime/certs/ca.crt)
```

## Script actif

| Script | Ce qu'il valide |
|---|---|
| `element-web.js` | chat : SSO immédiat → connexion → passage des dialogues de 1re session → ouverture salon → envoi d'un message visible |
| `meet.js` | visio : SSO automatique (contexte A) → création par l'UI → lien `/{slug}` → contexte B vierge : silent-login rebondi + re-login demo (login complet forcé) → Join (B éjecte A : *duplicate identity*, comportement amont) → contexte C invité anonyme → **2 participants** (badge topbar sur B et C) + websockets LiveKit |

## Usage

```powershell
npm i
$env:DEMO_PWD = (Select-String -Path "deployments/<client>/secrets.env" -Pattern '^demo_user_password=').Line.Split('=',2)[1]
node element-web.js
```

Meet (canal surchargeable, `chrome` sur les postes sans Edge) :

```bash
E2E_CHANNEL=chrome DEMO_PWD=... node meet.js
```

## Notes

- Les dialogues de 1re session Element Web (vérification, notifications) sont
  passés automatiquement : Skip verification → I'll verify later → Later →
  Dismiss. Les classes CSS-modules ne sont pas stables : on cible par texte.
- 404 bénignes filtrées : config.<domaine>.json (optionnelle), auth_metadata,
  dehydrated_device (MSC3814 optionnel).

## Meet — choix d'implémentation

- **Création de la réunion par l'UI** (et non par appel API direct) : le
  frontend fait lui-même le `POST /api/v1.0/rooms/` avec le cookie de session
  SSO (bouton « Create a meeting » → « Start an instant meeting »,
  sélecteurs `data-attr` amont stables). Le lien de partage est l'URL de la
  salle `https://meet.<domaine>/{slug}` (slug `[a-z]{3}-[a-z]{4}-[a-z]{3}`).
- **Contexte B** : hors page d'accueil, l'auto-login de la passerelle ne se
  déclenche pas ; le frontend tente un **silent-login** (`?silent=true` →
  `prompt=none`). Sans session Keycloak préalable, Keycloak répond
  `error=login_required` et rebondit sur la salle **non** authentifiée (fenêtre
  anti-retry de 30 s côté frontend) : le script détecte l'état non connecté
  (`users/me` = 401) et relance un **login complet** via l'URL exacte du bouton
  Login de l'app (`/api/v1.0/authenticate/?silent=false&returnTo=…`) →
  formulaire Keycloak → retour authentifié sur `/{slug}` (Join → Conference).
- **Identités LiveKit et critère « 2 participants »** : l'identité SFU d'un
  utilisateur authentifié est `user.sub` (amont `core/utils.generate_token`) —
  deux sessions du **même** compte SSO sur la même salle = éjection de la plus
  ancienne par LiveKit (écran produit « You have joined the meeting from
  another device », comportement conçu). Le second participant est donc un
  **invité anonyme** (contexte C, identité `uuid4` unique) : les salles créées
  sont publiques (`RESOURCE_DEFAULT_ACCESS_LEVEL=public` amont) et l'API y
  délivre un token sans session — chemin produit « invité sans compte ».
  `?silentLogin=false` (paramètre supporté par le frontend) évite le rebond
  du silent-login pour ce contexte.
- **Critère de réussite** : badge compteur du topbar (`aria-describedby` →
  span sr-only « N participants ») = 2 sur les DEUX pages + websockets
  `wss://livekit.…` ouvertes des deux côtés (média headless en bonus via
  `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream`).

## Meet — blocage déploiement connu (2026-10-23)

Sur le déploiement demo-coop actuel, le backend meet répond **400
`DisallowedHost` sur tout `/api/v1.0/*` et `/admin/`** : `meet v1.36.2`
(django-configurations) lit `DJANGO_ALLOWED_HOSTS` (préfixe `DJANGO_` par
défaut, cf. `docs/examples/helm/meet.values.yaml` amont qui utilise ce nom),
alors que `catalogue/meet.toml` `[env]` rend `ALLOWED_HOSTS=meet.localhost`
(dans `deployments/<client>/.runtime/meet.env`). Résultat :
`ALLOWED_HOSTS` vide au runtime → aucun appel Django ne passe (SSO, création,
whoami), alors que les healthchecks internes et le smoke restent verts.

Correction proposée (non appliquée ici) : renommer la clé en
`DJANGO_ALLOWED_HOSTS = "{app_bare}"` dans `catalogue/meet.toml`, rejouer le
rendu env + recréer le conteneur `meet_backend`. Le script détecte la page
« Bad Request (400) » et affiche ce diagnostic (capture
`e2e-meet-echec-400-backend.png`).
