# Tests E2E LaStarter (navigateur réel, Edge headless via playwright-core)

Volonté produit : **tout tester à chaque fois**. Ces scripts rejouent les
parcours client complets contre un déploiement actif (POC compris).

État : **un seul script actif, `element-web.js`** (chat). Les e2e meet de
l'ancienne brique de visio ont été retirés avec elle ; le parcours meet
(SSO → salon → invitation → appel) est à réécrire sur la brique
suitenumerique — voir [docs/ROADMAP.md](../../docs/ROADMAP.md).

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

## Usage

```powershell
npm i
$env:DEMO_PWD = (Select-String -Path "deployments/<client>/secrets.env" -Pattern '^demo_user_password=').Line.Split('=',2)[1]
node element-web.js
```

## Notes

- Les dialogues de 1re session Element Web (vérification, notifications) sont
  passés automatiquement : Skip verification → I'll verify later → Later →
  Dismiss. Les classes CSS-modules ne sont pas stables : on cible par texte.
- 404 bénignes filtrées : config.<domaine>.json (optionnelle), auth_metadata,
  dehydrated_device (MSC3814 optionnel).
