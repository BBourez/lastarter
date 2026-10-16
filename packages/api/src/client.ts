/*
 * LaStarter API : client HTTP base sur Ky.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import ky, { type KyInstance, type Options } from "ky";

export interface ApiClientConfig {
    /** URL de base de l'API (ex: /api/v1.0). */
    baseUrl: string;
    /** Token d'acces Bearer (recupere de la session). */
    getAccessToken?: () => string | undefined;
    /** Callback quand un 401 est recu (rediriger vers SSO). */
    onUnauthorized?: () => void;
}

/** Cree un client Ky configure avec interceptors auth et gestion 401. */
export function createApiClient(config: ApiClientConfig): KyInstance {
    return ky.create({
        prefixUrl: config.baseUrl,
        hooks: {
            beforeRequest: [
                (request) => {
                    const token = config.getAccessToken?.();
                    if (token) {
                        request.headers.set("Authorization", `Bearer ${token}`);
                    }
                },
            ],
            afterResponse: [
                (_request, _options, response) => {
                    if (response.status === 401) {
                        config.onUnauthorized?.();
                    }
                    return response;
                },
            ],
        },
        timeout: 30_000,
        retry: { limit: 2, methods: ["get"], statusCodes: [408, 502, 503] },
    });
}

/** GET generique type. */
export async function apiGet<T>(client: KyInstance, path: string, options?: Options): Promise<T> {
    return client.get(path, options).json<T>();
}

/** POST generique type. */
export async function apiPost<T, B = unknown>(
    client: KyInstance,
    path: string,
    body?: B,
    options?: Options,
): Promise<T> {
    return client.post(path, { json: body, ...options }).json<T>();
}

/** PUT generique type. */
export async function apiPut<T, B = unknown>(
    client: KyInstance,
    path: string,
    body?: B,
    options?: Options,
): Promise<T> {
    return client.put(path, { json: body, ...options }).json<T>();
}

/** DELETE generique type. */
export async function apiDelete<T>(
    client: KyInstance,
    path: string,
    options?: Options,
): Promise<T> {
    return client.delete(path, options).json<T>();
}
