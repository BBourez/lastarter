/*
Copyright 2022-2024 New Vector Ltd.

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial
Please see LICENSE in the repository root for full details.
*/

import { useCallback } from "react";
import { createClient } from "matrix-js-sdk";
import { logger } from "matrix-js-sdk/lib/logger";

import { useClient } from "../ClientContext";
import { generateRandomName } from "../auth/generateRandomName";
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

      // LaStarter : l'inscription complète est fermée (SSO only) — on crée
      // un compte INVITÉ (kind=guest, pas de mot de passe) et on pose le
      // nom affiché. Synapse attribue @N:domaine automatiquement.
      const baseUrl = Config.defaultHomeserverUrl()!;
      const authClient = createClient({ baseUrl });
      const creds = await authClient.registerRequest(
        {},
        undefined,
        { kind: "guest" },
      );
      const client = await initClient(
        {
          baseUrl,
          accessToken: creds.access_token,
          userId: creds.user_id,
          deviceId: creds.device_id,
        },
        false,
      );
      await client.setDisplayName(displayName);
      const user = client.getUser(client.getUserId()!)!;
      user.setRawDisplayName(displayName);
      user.setDisplayName(displayName);
      setClient(client, {
        user_id: creds.user_id,
        device_id: creds.device_id,
        access_token: creds.access_token,
        passwordlessUser: true,
      });
      logger.info(`Registered guest ${creds.user_id} as ${displayName}`);
    },
    [setClient, isWidget],
  );

  return { privacyPolicyUrl: undefined, registerPasswordlessUser };
}
