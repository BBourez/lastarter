# branding/ — thèmes clients (phase 2)

Identité graphique injectée par variables d'environnement (stratégie 80/20 —
voir docs/architecture.md §5) :

- `default.toml` — palette LaStarter par défaut (valeurs de surcharge des
  `[branding.env]` du catalogue).
- `<client>.toml` — surcharge par client (logo, couleurs, textes).

Aucun patch de code : chaque app consomme son thème via ses variables white-label
(drive : `FRONTEND_THEME`, `DJANGO_EMAIL_BRAND_NAME`… ; chat : `custom_themes`
element-web avec palette + overrides des tokens Compound — cf. catalogue/element-web.toml).
