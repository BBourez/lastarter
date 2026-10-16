/*
 * LaStarter API : TanStack Query client partage.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { QueryClient } from "@tanstack/react-query";

/** QueryClient global partage entre toutes les apps LaStarter. */
export function createQueryClient(): QueryClient {
    return new QueryClient({
        defaultOptions: {
            queries: {
                staleTime: 60_000,
                gcTime: 300_000,
                retry: 2,
                refetchOnWindowFocus: false,
            },
            mutations: {
                retry: 0,
            },
        },
    });
}
