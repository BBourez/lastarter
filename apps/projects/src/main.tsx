/*
 * LaStarter Projects : gestion de projets kanban.
 * Frontend neuf avec @lastarter/ui (Sidebar double colonne Element Web).
 * Backend Sails.js existant (API /api/).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { apiGet, createApiClient, createQueryClient } from "@lastarter/api";
import type { Board, Card, Project } from "@lastarter/api";
import { requireAuth } from "@lastarter/config";
import { detectLocale, initI18n, useTranslation } from "@lastarter/i18n";
import { Badge, Button, type NavSection, Sidebar, type Space, type User } from "@lastarter/ui";
import { QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { createRoot } from "react-dom/client";

/* Client HTTP pour Projects (backend Sails.js). */
const client = createApiClient({
    baseUrl: "/api",
    onUnauthorized: () => {
        window.location.replace("/login");
    },
});

/* ==================== HOOKS ==================== */

function useProjects() {
    return useQuery({
        queryKey: ["projects"],
        queryFn: () => apiGet<Project[]>(client, "projects/"),
    });
}

function useBoards(projectId: string | undefined) {
    return useQuery({
        queryKey: ["boards", projectId],
        queryFn: () => apiGet<Board[]>(client, `projects/${projectId}/boards/`),
        enabled: !!projectId,
    });
}

function useCurrentUser() {
    return useQuery({
        queryKey: ["user", "me"],
        queryFn: () => apiGet<{ email: string; full_name: string }>(client, "users/me/"),
    });
}

/* ==================== PAGE : TABLEAU KANBAN ==================== */

function KanbanBoard({ board }: { board: Board }) {
    const { t } = useTranslation();
    const [draggedCard, setDraggedCard] = useState<Card | null>(null);

    return (
        <div style={{ padding: "24px", height: "100%", overflowX: "auto" }}>
            <h2 style={{ marginBottom: 20 }}>{board.name}</h2>
            <div style={{ display: "flex", gap: 16, minHeight: "calc(100vh - 120px)" }}>
                {board.lists?.map((list) => (
                    <div
                        key={list.id}
                        style={{
                            flex: "0 0 280px",
                            background: "var(--ls-color-bg-subtle)",
                            borderRadius: "var(--ls-radius-md)",
                            padding: 12,
                            display: "flex",
                            flexDirection: "column",
                            gap: 8,
                        }}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={() => setDraggedCard(null)}
                    >
                        <div style={{ fontWeight: 600, fontSize: 14, padding: "4px 8px" }}>
                            {list.name}
                            <Badge variant="neutral" style={{ marginLeft: 8 }}>
                                {list.cards?.length ?? 0}
                            </Badge>
                        </div>
                        {list.cards?.map((card) => (
                            <div
                                key={card.id}
                                draggable
                                onDragStart={() => setDraggedCard(card)}
                                style={{
                                    background: "var(--ls-color-bg)",
                                    borderRadius: "var(--ls-radius-md)",
                                    border: "1px solid var(--ls-color-border)",
                                    padding: "10px 14px",
                                    cursor: "grab",
                                    fontSize: 14,
                                }}
                            >
                                <div style={{ fontWeight: 500 }}>{card.title}</div>
                                {card.due_date && (
                                    <div
                                        style={{
                                            fontSize: 12,
                                            color: "var(--ls-color-text-secondary)",
                                            marginTop: 4,
                                        }}
                                    >
                                        Echeance : {new Date(card.due_date).toLocaleDateString()}
                                    </div>
                                )}
                            </div>
                        ))}
                        <button
                            type="button"
                            style={{
                                border: "none",
                                background: "transparent",
                                color: "var(--ls-color-text-secondary)",
                                padding: "8px",
                                borderRadius: "var(--ls-radius-md)",
                                cursor: "pointer",
                                fontSize: 13,
                                textAlign: "left",
                            }}
                        >
                            + Ajouter une carte
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ==================== APP ==================== */

function ProjectsApp() {
    const { t } = useTranslation();
    const [activeProject, setActiveProject] = useState<string>();
    const [activeBoard, setActiveBoard] = useState<string>();
    const projectsQuery = useProjects();
    const boardsQuery = useBoards(activeProject);
    const userQuery = useCurrentUser();

    const user: User = {
        id: "me",
        displayName: userQuery.data?.full_name ?? "...",
        email: userQuery.data?.email ?? "",
    };

    const projects = projectsQuery.data ?? [];
    const boards = boardsQuery.data ?? [];

    const spaces: Space[] = projects.map((p) => ({
        id: p.id,
        label: p.name,
    }));

    const currentBoard = boards.find((b) => b.id === activeBoard) ?? boards[0];

    const sections: NavSection[] = [
        {
            id: "boards",
            title: t("nav.projectsBoards"),
            items: boards.map((b) => ({
                id: b.id,
                label: b.name,
                active: b.id === (activeBoard ?? currentBoard?.id),
                onClick: () => setActiveBoard(b.id),
            })),
        },
    ];

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <Sidebar
                spaces={spaces}
                activeSpaceId={activeProject ?? projects[0]?.id}
                onSpaceClick={(s) => {
                    setActiveProject(s.id);
                    setActiveBoard(undefined);
                }}
                onSpaceCreate={() => {
                    /* TODO : modal creation projet */
                }}
                sections={sections}
                user={user}
                searchPlaceholder={t("common.search")}
                onSettingsClick={() => {
                    /* TODO : page settings */
                }}
            />
            <main style={{ flex: 1, overflowY: "auto", background: "var(--ls-color-bg)" }}>
                {currentBoard ? (
                    <KanbanBoard board={currentBoard} />
                ) : (
                    <div
                        style={{
                            padding: 48,
                            textAlign: "center",
                            color: "var(--ls-color-text-secondary)",
                        }}
                    >
                        {projectsQuery.isLoading
                            ? "Chargement..."
                            : "Selectionnez ou creez un projet"}
                    </div>
                )}
            </main>
        </div>
    );
}

/* ==================== BOOT ==================== */

const queryClient = createQueryClient();
const locale = detectLocale();

requireAuth("projects");

initI18n(locale).then(() => {
    createRoot(document.getElementById("root")!).render(
        <QueryClientProvider client={queryClient}>
            <ProjectsApp />
        </QueryClientProvider>,
    );
});
