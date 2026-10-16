/*
 * LaStarter API : exports publics.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Client HTTP */
export { createApiClient, apiGet, apiPost, apiPut, apiDelete } from "./client";
export type { ApiClientConfig } from "./client";

/* TanStack Query */
export { createQueryClient } from "./query-client";

/* Schemas Zod (contrats partages, cf. Grafikart typing-e2e) */
export {
    PaginatedSchema,
    ApiErrorSchema,
    CurrentUserSchema,
    TransferStatusSchema,
    TransferFileSchema,
    TransferSchema,
    CreateTransferPayloadSchema,
    CardSchema,
    BoardListSchema,
    BoardSchema,
    ProjectSchema,
    CreateCardPayloadSchema,
    UpdateCardPayloadSchema,
} from "./schemas";

/* Types infers des schemas (z.infer) */
export type {
    CurrentUser,
    TransferStatus,
    TransferFile,
    Transfer,
    CreateTransferPayload,
    Card,
    BoardList,
    Board,
    Project,
    CreateCardPayload,
    UpdateCardPayload,
} from "./schemas";

/* Utils */
export { formatFileSize } from "./utils";
