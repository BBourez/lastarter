/*
 * Tests des schemas Zod (contrats API).
 * TDD : ces tests definissent le contrat attendu entre frontend et backend.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { describe, expect, it } from "vitest";
import {
    CardSchema,
    CreateCardPayloadSchema,
    CreateTransferPayloadSchema,
    CurrentUserSchema,
    ProjectSchema,
    TransferSchema,
} from "./schemas";

describe("CurrentUserSchema", () => {
    it("valide un utilisateur correct", () => {
        const user = {
            id: "123",
            email: "jean@acme.com",
            full_name: "Jean Dupont",
            language: "fr",
            is_staff: false,
        };
        expect(CurrentUserSchema.parse(user)).toEqual(user);
    });

    it("rejette un email invalide", () => {
        const user = {
            id: "123",
            email: "pas-un-email",
            full_name: "Jean",
            language: "fr",
            is_staff: false,
        };
        expect(() => CurrentUserSchema.parse(user)).toThrow();
    });
});

describe("TransferSchema", () => {
    const validTransfer = {
        id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        status: "sent",
        emails: ["jean@acme.com"],
        files: [
            {
                id: "file-1",
                name: "document.pdf",
                size: 1024,
                content_type: "application/pdf",
                download_url: "https://example.com/file",
            },
        ],
        created_at: "2026-01-01T00:00:00Z",
        download_count: 0,
    };

    it("valide un transfert correct", () => {
        const result = TransferSchema.parse(validTransfer);
        expect(result.status).toBe("sent");
        expect(result.files).toHaveLength(1);
    });

    it("rejette un status invalide", () => {
        expect(() => TransferSchema.parse({ ...validTransfer, status: "invalid" })).toThrow();
    });

    it("rejette un UUID invalide", () => {
        expect(() => TransferSchema.parse({ ...validTransfer, id: "pas-un-uuid" })).toThrow();
    });

    it("rejette un download_count negatif", () => {
        expect(() => TransferSchema.parse({ ...validTransfer, download_count: -1 })).toThrow();
    });
});

describe("CreateTransferPayloadSchema", () => {
    it("valide un payload correct", () => {
        const payload = {
            emails: ["jean@acme.com", "marie@acme.com"],
            duration: "7_days",
        };
        expect(CreateTransferPayloadSchema.parse(payload)).toEqual(payload);
    });

    it("rejette une liste d'emails vide", () => {
        expect(() =>
            CreateTransferPayloadSchema.parse({ emails: [], duration: "7_days" }),
        ).toThrow();
    });

    it("rejette une duree invalide", () => {
        expect(() =>
            CreateTransferPayloadSchema.parse({ emails: ["a@b.com"], duration: "100_days" }),
        ).toThrow();
    });
});

describe("ProjectSchema", () => {
    it("valide un projet avec boards et cartes", () => {
        const project = {
            id: "proj-1",
            name: "Site web",
            boards: [
                {
                    id: "board-1",
                    project_id: "proj-1",
                    name: "Sprint 1",
                    slug: "sprint-1",
                    lists: [
                        {
                            id: "list-1",
                            board_id: "board-1",
                            name: "A faire",
                            position: 0,
                            cards: [
                                {
                                    id: "card-1",
                                    list_id: "list-1",
                                    title: "Creer la page d'accueil",
                                    position: 0,
                                    created_at: "2026-01-01T00:00:00Z",
                                    updated_at: "2026-01-01T00:00:00Z",
                                },
                            ],
                        },
                    ],
                    created_at: "2026-01-01T00:00:00Z",
                },
            ],
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        };
        const result = ProjectSchema.parse(project);
        expect(result.boards[0]?.lists[0]?.cards[0]?.title).toBe("Creer la page d'accueil");
    });
});

describe("CardSchema", () => {
    it("rejette un titre vide", () => {
        const card = {
            id: "card-1",
            list_id: "list-1",
            title: "",
            position: 0,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
        };
        expect(() => CardSchema.parse(card)).toThrow();
    });
});

describe("CreateCardPayloadSchema", () => {
    it("valide un payload de carte correct", () => {
        const payload = {
            list_id: "list-1",
            title: "Nouvelle tache",
        };
        expect(CreateCardPayloadSchema.parse(payload)).toEqual(payload);
    });

    it("rejette un payload sans titre", () => {
        expect(() => CreateCardPayloadSchema.parse({ list_id: "list-1", title: "" })).toThrow();
    });
});
