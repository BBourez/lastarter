# Patch SSO natif - Element Call

Applique sur le checkout `examples-inspiration/element-call` :

1. `src/auth/SsoAutoRedirect.tsx` (nouveau) : composant d'auto-SSO -
   redirige vers `sso_redirect_base_url` (chat) + echange le `#loginToken`.
2. `src/home/HomePage.tsx` : la vue non authentifiee = SsoAutoRedirect
   (plus de UnauthenticatedView login/register/guest).
3. `src/room/RoomPage.tsx` : RoomAuthView remplacee par SsoAutoRedirect.

Build : `pnpm install && pnpm build` puis `docker build -f Dockerfile.lastarter
-t lastarter/element-call:sso .` (image servie par la brique element-call).

Cle de config : `"sso_redirect_base_url": "https://chat.<domaine>"` generee
par le CLI (le kickoff SSO pose le cookie Synapse sur l'origine du callback).

## v2 : fix boucle SSO (loginToken perdu au boot)

- `main.tsx` : capture le loginToken AVANT le montage React (stash
  `window.__lsLoginToken` + nettoyage du fragment).
- `SsoAutoRedirect` : lit le stash en priorite, consomme le stash,
  et NE relance PAS le SSO en cas d'echec d'echange (anti-boucle).

## v3 : le loginToken arrive en QUERY (pas fragment)

Capture du HAR : Synapse renvoie `?loginToken=` (query string) et non
`#loginToken=`. `main.tsx` capture les DEUX formes (hash + query),
l'URL est nettoyee (pathname seul).

## v4 : liens d'invitation + menus

- `RoomPage` : RoomAuthView restauree pour les liens de salon (join en
  guest avec juste un pseudo ; les sessions SSO ne la voient jamais).
- `RoomAuthView` : footer « Create an account » supprime.
- `index.css` : override des bordures parasites au survol des elements
  de menu Compound (outline/border/box-shadow none).

## v5 : salons invitable par guests

`utils/matrix.ts` createRoom : initial_state `m.room.guest_access`
= `can_join` (le champ guest_access de createRoom est IGNORE par Synapse,
et la valeur spec est « can_join », pas « guest »).
