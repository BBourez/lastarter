/*
 * LaStarter Transfers : hooks API (TanStack Query).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createApiClient, apiGet, apiPost, type Transfer } from "@lastarter/api";

/* Client HTTP configure pour Transfers (backend Django). */
const client = createApiClient({
    baseUrl: "/api/v1.0",
    onUnauthorized: () => {
        window.location.replace("/api/v1.0/authenticate/");
    },
});

/* ==================== HOOKS ==================== */

/** Recuperer la liste des transferts envoyes. */
export function useSentTransfers() {
    return useQuery({
        queryKey: ["transfers", "sent"],
        queryFn: () => apiGet<Transfer[]>(client, "transfers/sent/"),
    });
}

/** Recuperer la liste des transferts recus. */
export function useReceivedTransfers() {
    return useQuery({
        queryKey: ["transfers", "received"],
        queryFn: () => apiGet<Transfer[]>(client, "transfers/received/"),
    });
}

/** Recuperer un transfert par ID. */
export function useTransfer(id: string) {
    return useQuery({
        queryKey: ["transfers", id],
        queryFn: () => apiGet<Transfer>(client, `transfers/${id}/`),
    });
}

/** Creer un nouveau transfert (upload de fichiers). */
export function useCreateTransfer() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: {
            emails: string[];
            files: File[];
            message?: string;
            duration: string;
        }) => {
            const formData = new FormData();
            for (const email of data.emails) formData.append("emails", email);
            for (const file of data.files) formData.append("files", file);
            if (data.message) formData.append("message", data.message);
            formData.append("duration", data.duration);
            return client.post("transfers/", { body: formData }).json<Transfer>();
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["transfers"] });
        },
    });
}

/** Recuperer l'utilisateur courant. */
export function useCurrentUser() {
    return useQuery({
        queryKey: ["user", "me"],
        queryFn: () => apiGet<{ email: string; full_name: string }>(client, "users/me/"),
    });
}
