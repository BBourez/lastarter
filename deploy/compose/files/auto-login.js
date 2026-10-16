// LaStarter â€” auto-redirect SSO.
// L'URL d'auth vient de l'attribut data-auth du <script> qui charge ce fichier
// (rendu par le CLI : /api/v1.0/authenticate/ pour Django, /login pour Projects).
// Anti-boucle : sessionStorage flag (une seule tentative par onglet).
(() => {
    if (sessionStorage.getItem("ls_auth_redirect")) return;
    const script = document.currentScript || document.querySelector("script[data-auth]");
    if (!script) return;
    const authUrl = script.getAttribute("data-auth");
    if (!authUrl) return;
    const hasSession = document.cookie.indexOf("sessionid=") !== -1;
    const path = window.location.pathname;
    if (!hasSession && (path === "/" || path === "")) {
        sessionStorage.setItem("ls_auth_redirect", "1");
        window.location.replace(authUrl);
    }
})();
