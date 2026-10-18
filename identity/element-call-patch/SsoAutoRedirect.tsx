/*
Copyright 2026 LaStarter

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial
Please see LICENSE files in the repository root for full details.
*/

import { type FC, useEffect } from "react";
import { createClient } from "matrix-js-sdk";

import { useClient } from "../ClientContext";
import { Config } from "../config/Config";
import { LoadingPage } from "../FullScreenView";
import { initClient } from "../utils/matrix";

/**
 * SSO natif LaStarter : comme Element Web —
 * 1. si l'URL contient #loginToken (retour du SSO), l'échanger contre une
 *    session Matrix (m.login.token) et se connecter ;
 * 2. sinon rediriger vers le SSO du homeserver (Synapse OIDC → Keycloak).
 * Aucune page de login/register/guest n'est jamais affichée.
 *
 * Le kickoff SSO utilise l'origine du homeserver PUBLIC (chat.<domaine>) :
 * Synapse y pose son cookie de session SSO et y reçoit le callback OIDC —
 * l'échange loginToken, lui, reste same-origin (meet).
 */
export const SsoAutoRedirect: FC = () => {
  const { setClient } = useClient();

  useEffect(() => {
    let cancelled = false;
    const baseUrl = Config.defaultHomeserverUrl();

    const ssoKickoff = (ssoBase: string) => {
      const redirect = encodeURIComponent(
        window.location.origin + window.location.pathname,
      );
      window.location.href = `${ssoBase}/_matrix/client/v3/login/sso/redirect?redirectUrl=${redirect}`;
    };

    const match =
      (window as { __lsLoginToken?: string }).__lsLoginToken ??
      window.location.hash.match(/loginToken=([^&]+)/)?.[1] ??
      window.location.search.match(/loginToken=([^&]+)/)?.[1] ??
      null;

    if (!match) {
      // Origine du kickoff : clé LaStarter du config, sinon le homeserver.
      fetch("/config.json")
        .then((r) => (r.ok ? r.json() : ({} as Record<string, unknown>)))
        .then((cfg: Record<string, unknown>) => {
          if (cancelled) return;
          ssoKickoff(
            typeof cfg.sso_redirect_base_url === "string"
              ? cfg.sso_redirect_base_url
              : baseUrl,
          );
        })
        .catch(() => {
          if (!cancelled) ssoKickoff(baseUrl);
        });
      return;
    }

    const token = match;
    // Consommer le stash + nettoyer le fragment pour éviter les rejeux.
    delete (window as { __lsLoginToken?: string }).__lsLoginToken;
    window.history.replaceState(null, "", window.location.pathname);
    const authClient = createClient({ baseUrl });
    authClient
      .login("m.login.token", { token })
      .then(async ({ user_id, access_token, device_id }) => {
        if (cancelled) return;
        const client = await initClient(
          {
            baseUrl,
            accessToken: access_token,
            userId: user_id,
            deviceId: device_id,
          },
          false,
        );
        if (cancelled || !setClient) return;
        setClient(client, {
          user_id,
          access_token,
          device_id,
          passwordlessUser: false,
        });
      })
      .catch((error) => {
        // PAS de retry automatique : un loginToken rejoué bouclerait le flux
        // SSO à l'infini. L'utilisateur recharge la page pour un nouveau flux.
        console.error("SSO loginToken exchange failed", error);
      });
    return () => {
      cancelled = true;
    };
  }, [setClient]);

  return <LoadingPage />;
};
