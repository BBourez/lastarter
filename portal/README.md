# portal/ — portail SSO (phase 5)

Point d'entrée unique du déploiement : launchpad des briques activées pour
l'utilisateur, session Keycloak partagée, notifications.

Construit sur base **permissive** (Radix/shadcn + Tailwind), ergonomie inspirée
d'Element — sans incorporer le code AGPL de Compound (cf. docs/licences.md).

C'est la surface où l'identité LaStarter s'exprime le plus fort ; v1 volontairement
mince (une page, pas d'usine), réévaluation de `hub` amont en parallèle.
