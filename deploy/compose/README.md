# deploy/compose/ — cible mono-VM

`base.yml` (socle commun) + **un fichier par brique** (`<brique>.yml`).
Pas de réseau externe partagé : `base.yml` définit un réseau bridge propre au
projet (`lastarter-<client>`) — et pas de « profils » compose : l'assemblage
se fait par accumulation de `-f`.

`lastarter deploy` assemble et lance :

```
docker compose --env-file <runtime>/compose.env -p <client> \
  -f base.yml -f <brique>.yml …
```

Les env de chaque brique viennent de `deployments/<client>/env/*.env` (jetons
`{secret:…}` substitués depuis `secrets.env` au moment du déploiement, jamais
commités).
