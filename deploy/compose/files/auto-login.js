// LaStarter — auto-redirect SSO (pas de landing page).
// Sert sur /__lastarter/auto-login.js sur toutes les apps.
// Si l'utilisateur n'a pas de session Django et qu'il est sur /, redirige vers l'auth.
(function () {
    "use strict";
    var hasSession =
        document.cookie.indexOf("sessionid=") !== -1 ||
        document.cookie.indexOf("csrftoken=") !== -1;
    var path = window.location.pathname;
    // Uniquement la racine (pas /callback, pas /oidc-callback, etc.)
    if (!hasSession && (path === "/" || path === "")) {
        window.location.replace("/api/v1.0/authenticate/");
    }
})();
