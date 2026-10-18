/*
Copyright 2022-2024 New Vector Ltd.

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial
Please see LICENSE in the repository root for full details.
*/

import { useCallback } from "react";
import { createClient } from "matrix-js-sdk";
import { logger } from "matrix-js-sdk/lib/logger";

import { useClient } from "../ClientContext";
import { initClient } from "../utils/matrix";
import { Config } from "../config/Config";
import { useUrlParams } from "../UrlParams";

interface UseRegisterPasswordlessUserType {
  privacyPolicyUrl?: string;
  registerPasswordlessUser: (displayName: string) => Promise<void>;
  recaptchaId?: string;
}

export function useRegisterPasswordlessUser(): UseRegisterPasswordlessUserType {
  const { setClient } = useClient();
  const { isWidget } = useUrlParams();

  const registerPasswordlessUser = useCallback(
    async (displayName: string) => {
      if (!setClient) {
        throw new Error("No client context");
      }
      if (isWidget) {
        throw new Error(
          "Registration was skipped: We should never try to register password-less user in embedded mode.",
        );
      }

      // LaStarter : les comptes « guest » de Synapse ne peuvent pas obtenir
      // de jeton OpenID (M_GUEST_ACCESS_FORBIDDEN) donc pas rejoindre l'appel
      // SFU. Le registrar de la passerelle crée un VRAI compte pseudo-seul
      // (via le shared secret, côté serveur) et pose le nom affiché.
      const baseUrl = Config.defaultHomeserverUrl()!;
      const res = await fetch("/_lastarter/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ display_name: displayName }),
      });
      if (!res.ok) {
        throw new Error(
          `Guest registrar failed: ${res.status} ${await res.text()}`,
        );
      }
      const creds = (await res.json()) as {
        user_id: string;
        access_token: string;
        device_id: string;
      };

      const client = await initClient(
        {
          baseUrl,
          accessToken: creds.access_token,
          userId: creds.user_id,
          deviceId: creds.device_id,
        },
        false,
      );
      const user = client.getUser(client.getUserId()!)!;
      user.setRawDisplayName(displayName);
      user.setDisplayName(displayName);
      setClient(client, {
        user_id: creds.user_id,
        device_id: creds.device_id,
        access_token: creds.access_token,
        passwordlessUser: true,
      });
      logger.info(
        `Registered invite ${creds.user_id} as ${displayName}`,
      );
    },
    [setClient, isWidget],
  );

  return { privacyPolicyUrl: undefined, registerPasswordlessUser };
}
