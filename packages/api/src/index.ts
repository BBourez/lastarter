/*
 * LaStarter API : exports publics.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Client HTTP */
export { createApiClient, apiGet, apiPost, apiPut, apiDelete } from "./client";
export type { ApiClientConfig } from "./client";

/* TanStack Query */
export { createQueryClient } from "./query-client";

/* Types metier */
export type {
    Paginated,
    ApiError,
    CurrentUser,
    Transfer,
    TransferFile,
    TransferStatus,
    CreateTransferPayload,
    Project,
    Board,
    BoardList,
    Card,
    CreateCardPayload,
    UpdateCardPayload,
} from "./types";
