# Tests E2E LaStarter (navigateur reel, Edge headless via Playwright)

Volonte produit : **tout tester a chaque fois**. Ces scripts rejouent les
parcours client complets contre un deploiement actif (POC compris).

## Prerequis

```powershell
npm i playwright-core            # dans un dossier de travail
# Edge est utilise via channel:msedge (aucun telechargement de navigateur)
# La CA du deploiement doit etre dans le magasin Windows (fait par le CLI/POC)
```

## Scripts

| Script            | Ce qu'il valide                                                       |
| ----------------- | --------------------------------------------------------------------- |
| `element-web.js`  | chat : SSO immediat -> connexion -> passage des dialogues 1re session -> ouverture salon -> envoi d'un message visible |
| `meet.js`         | meet : SSO -> creation de reunion -> lien d'invitation -> contexte VIERGE (navigation privee) -> pseudo -> UI d'appel chiffree pour les DEUX participants |
| `meet-invitation.js` | meet : un lien d'invitation precis (const URL) en contexte vierge    |

## Usage

```powershell
$env:DEMO_PWD = (Select-String -Path "deployments/<client>/secrets.env" -Pattern '^demo_user_password=').Line.Split('=',2)[1]
node scripts/e2e/element-web.js
node scripts/e2e/meet.js
```

## Notes

- Les dialogues de 1re session Element Web (verification, notifications) sont
  passes automatiquement : Skip verification -> I'll verify later -> Later ->
  Dismiss. Les classes CSS-modules ne sont pas stables : on cible par texte.
- 404 benignes filtree : config.<domaine>.json (optionnelle), auth_metadata,
  dehydrated_device (MSC3814 optionnel).
