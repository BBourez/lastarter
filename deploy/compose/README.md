# deploy/compose/ — cible mono-VM (phase 2)

Docker-compose de base + un profil par brique (modèle `lasuite-network` observé
dans les compose amont : réseau externe partagé entre briques).

`lastarter deploy` (phase 2) assemble : compose de base + profils des briques du
manifeste client, env depuis `deployments/<client>/env/*.env` (jetons `{secret:…}`
substitués depuis secrets.env au moment du déploiement, jamais commités).
