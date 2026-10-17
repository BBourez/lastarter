/*
 * LaStarter Projects : kanban avec ElementShell (vrais composants Compound).
 * Backend Sails.js existant (API /api/).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Les vrais tokens + styles Compound */
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-base.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-semantic.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-font-fallbacks.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-theme-light-base-mq.css";
import "@vector-im/compound-web/dist/style.css";

import { apiGet, createApiClient, createQueryClient } from "@lastarter/api";
import type { Board, Card, Project } from "@lastarter/api";
import { ElementShell, type ShellModule } from "@lastarter/ui";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Badge, Body, Heading } from "@vector-im/compound-web";
import "./projects.css";

/* Client HTTP pour Projects (backend Sails.js). */
const client = createApiClient({
    baseUrl: "/api",
    onUnauthorized: () => {
        window.location.replace("/login");
    },
});

/* Modules du LeftPanel pour cette app */
const MODULES: ShellModule[] = [
    { id: "transfers", label: "Transferts", url: "http://transfers.localhost/" },
    { id: "projects", label: "Projets", url: "http://projects.localhost/" },
    { id: "chat", label: "Discussions", url: "http://chat.localhost/", badge: 3 },
    { id: "meet", label: "Reunions", url: "http://meet.localhost/" },
];

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

/* ==================== KANBAN ==================== */

function KanbanBoard({ board }: { board: Board }) {
    const [draggedCard, setDraggedCard] = useState<Card | null>(null);

    return (
        <div className="pr_Board">
            <Heading size="md" weight="medium">{board.name}</Heading>
            <div className="pr_Columns">
                {board.lists?.map((list) => (
                    <div
                        key={list.id}
                        className="pr_Column"
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={() => setDraggedCard(null)}
                    >
                        <div className="pr_ColumnHeader">
                            {list.name}
                            <Badge count={list.cards?.length ?? 0} />
                        </div>
                        {list.cards?.map((card) => (
                            <div
                                key={card.id}
                                className="pr_Card"
                                draggable
                                onDragStart={() => setDraggedCard(card)}
                            >
                                <div className="pr_CardTitle">{card.title}</div>
                                {card.due_date && (
                                    <div className="pr_CardDue">
                                        Echeance : {new Date(card.due_date).toLocaleDateString()}
                                    </div>
                                )}
                            </div>
                        ))}
                        <button type="button" className="pr_AddCard">
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
    const [activeProject, setActiveProject] = useState<string>();
    const [activeBoard, setActiveBoard] = useState<string>();
    const projectsQuery = useProjects();
    const boardsQuery = useBoards(activeProject);

    const projects = projectsQuery.data ?? [];
    const boards = boardsQuery.data ?? [];
    const currentBoard = boards.find((b) => b.id === activeBoard) ?? boards[0];

    /* Les tableaux du projet actif dans le LeftPanel */
    const modules: ShellModule[] = [
        ...projects.map((p) => ({
            id: `project-${p.id}`,
            label: p.name,
            url: `?project=${p.id}`,
        })),
        ...boards.map((b) => ({
            id: `board-${b.id}`,
            label: `  ${b.name}`,
            url: `?board=${b.id}`,
        })),
    ];

    return (
        <ElementShell
            modules={modules.length > 0 ? modules : MODULES}
            activeModuleId={currentBoard ? `board-${currentBoard.id}` : "projects"}
        >
            <header className="ls_PageHeader">
                <Body as="h1" size="lg" weight="medium">Projets</Body>
            </header>
            <div className="ls_PageBody">
                {currentBoard ? (
                    <KanbanBoard board={currentBoard} />
                ) : (
                    <Body size="md" className="pr_Muted">
                        {projectsQuery.isLoading
                            ? "Chargement..."
                            : "Selectionnez ou creez un projet"}
                    </Body>
                )}
            </div>
        </ElementShell>
    );
}

/* ==================== BOOT ==================== */

const queryClient = createQueryClient();

createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <ProjectsApp />
        </QueryClientProvider>
    </React.StrictMode>,
);
