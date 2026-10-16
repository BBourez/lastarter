/*
 * LaStarter API : types metier partages (DDD).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* ==================== COMMUN ==================== */

export interface Paginated<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export interface ApiError {
    code: string;
    message: string;
    details?: Record<string, string[]>;
}

/* ==================== UTILISATEUR ==================== */

export interface CurrentUser {
    id: string;
    email: string;
    full_name: string;
    language: string;
    is_staff: boolean;
}

/* ==================== TRANSFERS ==================== */

export type TransferStatus = "draft" | "pending" |"sent" | "deleted";

export interface Transfer {
    id: string;
    status: TransferStatus;
    emails: string[];
    files: TransferFile[];
    message?: string;
    subject?: string;
    created_at: string;
    expires_at?: string;
    download_count: number;
}

export interface TransferFile {
    id: string;
    name: string;
    size: number;
    content_type: string;
    download_url: string;
}

export interface CreateTransferPayload {
    emails: string[];
    files: File[];
    message?: string;
    subject?: string;
    duration: string;
    password?: string;
}

/* ==================== PROJECTS ==================== */

export interface Project {
    id: string;
    name: string;
    description?: string;
    boards: Board[];
    created_at: string;
    updated_at: string;
}

export interface Board {
    id: string;
    project_id: string;
    name: string;
    slug: string;
    lists: BoardList[];
    created_at: string;
}

export interface BoardList {
    id: string;
    board_id: string;
    name: string;
    position: number;
    cards: Card[];
}

export interface Card {
    id: string;
    list_id: string;
    title: string;
    description?: string;
    position: number;
    assignee?: CurrentUser;
    labels?: string[];
    due_date?: string;
    created_at: string;
    updated_at: string;
}

export interface CreateCardPayload {
    list_id: string;
    title: string;
    description?: string;
    assignee_id?: string;
    due_date?: string;
}

export interface UpdateCardPayload {
    title?: string;
    description?: string;
    position?: number;
    list_id?: string;
    assignee_id?: string | null;
}
