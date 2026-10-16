/*
 * LaStarter config : environnement + SSO.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* ==================== ENVIRONNEMENT ==================== */

/** Lire une variable d'environnement (Vite import.meta.env ou process.env). */
function readEnv(key: string): string | undefined {
    if (typeof import.meta !== "undefined" && import.meta.env) {
        return import.meta.env[key];
    }
    if (typeof process !== "undefined" && process.env) {
        return process.env[key];
    }
    return undefined;
}

export interface LaStarterEnv {
    domain: string;
    scheme: string;
    ssoOrigin: string;
    theme: string;
    brandName: string;
    brandColor: string;
}

/** Configuration d'environnement calculee (memoisee). */
let cachedEnv: LaStarterEnv | undefined;

export function getEnv(): LaStarterEnv {
    if (cachedEnv) return cachedEnv;
    const domain = readEnv("LASTARTER_DOMAIN") ?? "localhost:8443";
    const scheme = readEnv("LASTARTER_SCHEME") ?? "https";
    cachedEnv = {
        domain,
        scheme,
        ssoOrigin: `${scheme}://id.${domain}`,
        theme: readEnv("LASTARTER_THEME") ?? "element-light",
        brandName: readEnv("LASTARTER_BRAND_NAME") ?? "LaStarter",
        brandColor: readEnv("LASTARTER_BRAND_COLOR") ?? "#0bc491",
    };
    return cachedEnv;
}

/* ==================== AUTH (SSO Keycloak) ==================== */

export interface SsoConfig {
    issuer: string;
    clientId: string;
    redirectUri: string;
    scope: string;
}

/** Config SSO pour une app donnee (clientId different par app). */
export function getSsoConfig(appId: string): SsoConfig {
    const env = getEnv();
    return {
        issuer: `${env.ssoOrigin}/realms/lastarter`,
        clientId: appId,
        redirectUri: `${env.scheme}://${appId}.${env.domain}/callback`,
        scope: "openid email profile",
    };
}

/** URL de connexion SSO (redirige vers Keycloak). */
export function getSsoLoginUrl(appId: string): string {
    const config = getSsoConfig(appId);
    const params = new URLSearchParams({
        client_id: config.clientId,
        redirect_uri: config.redirectUri,
        response_type: "code",
        scope: config.scope,
    });
    return `${config.issuer}/protocol/openid-connect/auth?${params}`;
}

/** URL de logout SSO. */
export function getSsoLogoutUrl(appId: string): string {
    const config = getSsoConfig(appId);
    return `${config.issuer}/protocol/openid-connect/logout?client_id=${config.clientId}&post_logout_redirect_uri=${encodeURIComponent(config.redirectUri)}`;
}

/** Verifier si l'utilisateur a une session (cookie sessionid Django). */
export function hasSession(): boolean {
    if (typeof document === "undefined") return false;
    return document.cookie.includes("sessionid=");
}

/** Rediriger vers le SSO si pas de session (pas de page d'accueil). */
export function requireAuth(appId: string, authPath = "/api/v1.0/authenticate/"): void {
    if (typeof window === "undefined") return;
    if (!hasSession() && (window.location.pathname === "/" || window.location.pathname === "")) {
        const isSailsBackend = appId === "projects";
        window.location.replace(isSailsBackend ? "/login" : authPath);
    }
}
