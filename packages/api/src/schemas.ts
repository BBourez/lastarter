/*
 * LaStarter API : schemas Zod (contrats partages front/backend).
 * Approach : contrat-first avec Zod (cf. tutoriel Grafikart "Partager les types").
 * Les schemas servent a la fois de :
 *   1. Types TypeScript statiques (z.infer)
 *   2. Validation runtime (cote client pour les reponses API)
 *   3. Documentation vivante de l'API
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { z } from "zod";

/* ==================== COMMUN ==================== */

/** Schema de pagination Django REST Framework. */
export const PaginatedSchema = z.object({
    count: z.number(),
    next: z.string().nullable(),
    previous: z.string().nullable(),
    results: z.array(z.unknown()),
});

/** Schema d'erreur API. */
export const ApiErrorSchema = z.object({
    code: z.string(),
    message: z.string(),
    details: z.record(z.array(z.string())).optional(),
});

/* ==================== UTILISATEUR ==================== */

export const CurrentUserSchema = z.object({
    id: z.string(),
    email: z.string().email(),
    full_name: z.string(),
    language: z.string(),
    is_staff: z.boolean(),
});
export type CurrentUser = z.infer<typeof CurrentUserSchema>;

/* ==================== TRANSFERS ==================== */

export const TransferStatusSchema = z.enum(["draft", "pending", "sent", "deleted"]);
export type TransferStatus = z.infer<typeof TransferStatusSchema>;

export const TransferFileSchema = z.object({
    id: z.string(),
    name: z.string(),
    size: z.number().positive(),
    content_type: z.string(),
    download_url: z.string().url(),
});
export type TransferFile = z.infer<typeof TransferFileSchema>;

export const TransferSchema = z.object({
    id: z.string().uuid(),
    status: TransferStatusSchema,
    emails: z.array(z.string().email()),
    files: z.array(TransferFileSchema),
    message: z.string().optional(),
    subject: z.string().optional(),
    created_at: z.string().datetime(),
    expires_at: z.string().datetime().optional(),
    download_count: z.number().int().nonnegative(),
});
export type Transfer = z.infer<typeof TransferSchema>;

/** Payload de creation d'un transfert (validation cote client avant envoi). */
export const CreateTransferPayloadSchema = z.object({
    emails: z.array(z.string().email()).min(1, "Au moins un destinataire requis"),
    message: z.string().max(2000).optional(),
    subject: z.string().max(255).optional(),
    duration: z.enum(["1_days", "7_days", "14_days", "30_days"]),
});
export type CreateTransferPayload = z.infer<typeof CreateTransferPayloadSchema>;

/* ==================== PROJECTS ==================== */

export const CardSchema = z.object({
    id: z.string(),
    list_id: z.string(),
    title: z.string().min(1),
    description: z.string().optional(),
    position: z.number().int().nonnegative(),
    assignee: CurrentUserSchema.optional(),
    labels: z.array(z.string()).optional(),
    due_date: z.string().datetime().optional(),
    created_at: z.string().datetime(),
    updated_at: z.string().datetime(),
});
export type Card = z.infer<typeof CardSchema>;

export const BoardListSchema = z.object({
    id: z.string(),
    board_id: z.string(),
    name: z.string(),
    position: z.number().int().nonnegative(),
    cards: z.array(CardSchema),
});
export type BoardList = z.infer<typeof BoardListSchema>;

export const BoardSchema = z.object({
    id: z.string(),
    project_id: z.string(),
    name: z.string(),
    slug: z.string(),
    lists: z.array(BoardListSchema),
    created_at: z.string().datetime(),
});
export type Board = z.infer<typeof BoardSchema>;

export const ProjectSchema = z.object({
    id: z.string(),
    name: z.string().min(1),
    description: z.string().optional(),
    boards: z.array(BoardSchema),
    created_at: z.string().datetime(),
    updated_at: z.string().datetime(),
});
export type Project = z.infer<typeof ProjectSchema>;

/** Payload de creation d'une carte. */
export const CreateCardPayloadSchema = z.object({
    list_id: z.string(),
    title: z.string().min(1, "Titre requis"),
    description: z.string().optional(),
    assignee_id: z.string().optional(),
    due_date: z.string().datetime().optional(),
});
export type CreateCardPayload = z.infer<typeof CreateCardPayloadSchema>;

/** Payload de mise a jour d'une carte. */
export const UpdateCardPayloadSchema = z.object({
    title: z.string().min(1).optional(),
    description: z.string().optional(),
    position: z.number().int().nonnegative().optional(),
    list_id: z.string().optional(),
    assignee_id: z.string().nullable().optional(),
});
export type UpdateCardPayload = z.infer<typeof UpdateCardPayloadSchema>;
