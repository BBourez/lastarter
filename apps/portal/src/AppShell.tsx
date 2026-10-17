/*
 * LaStarter AppShell : structure identique a Element Web.
 * SpacePanel (68px) + LeftPanel (room list + user menu).
 * Utilise les VRAIS composants Compound (@vector-im/compound-web).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useState } from "react";
import {
    Avatar,
    Badge,
    Body,
    Button,
    IconButton,
    Search,
    Separator,
    TextButton,
    Tooltip,
} from "@vector-im/compound-web";
import "./portal.css";

/* ==================== ICONES (SVG inline, style Element) ==================== */

const HomeIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" {...props}>
        <path d="M10 2.5 2.5 9h2v8h4v-5h3v5h4V9h2L10 2.5Z" />
    </svg>
);

const FolderIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" {...props}>
        <path d="M2 4.5A1.5 1.5 0 0 1 3.5 3h4l2 2.5h5A1.5 1.5 0 0 1 16 7v7.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 2 14.5v-10Z" />
    </svg>
);

const ChatIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" {...props}>
        <path d="M3 4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H8l-4 3.5V14H5a2 2 0 0 1-2-2V4Z" />
    </svg>
);

const VideoIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" {...props}>
        <path d="M2 6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v1.5l3.3-2.3a1 1 0 0 1 1.7.8v8a1 1 0 0 1-1.7.8L13 12.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6Z" />
    </svg>
);

const TransferIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" {...props}>
        <path d="M10 2 6 6h3v6h2V6h3l-4-4ZM4 13v3a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-3h-2v3H6v-3H4Z" />
    </svg>
);

const ProjectIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" {...props}>
        <path d="M3 5a2 2 0 0 1 2-2h3.6a1 1 0 0 1 .8.4L10.8 5H15a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5Z" />
    </svg>
);

const SettingsIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" {...props}>
        <path d="M8 5.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Zm6.4 3.6.1-1.1-1.4-.6a5 5 0 0 0-.4-1l.6-1.4-.8-.8-1.4.6a5 5 0 0 0-1-.4L9.5 2.4H8.5l-.6 1.4a5 5 0 0 0-1 .4L5.5 3.6l-.8.8.6 1.4a5 5 0 0 0-.4 1l-1.4.6.1 1.1 1.4.6a5 5 0 0 0 .4 1l-.6 1.4.8.8 1.4-.6a5 5 0 0 0 1 .4l.6 1.4h1l.6-1.4a5 5 0 0 0 1-.4l1.4.6.8-.8-.6-1.4a5 5 0 0 0 .4-1l1.4-.6Z" />
    </svg>
);

const HelpIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" {...props}>
        <path d="M8 1.5A6.5 6.5 0 1 0 14.5 8 6.5 6.5 0 0 0 8 1.5Zm.7 10.8H7.2v-1.5h1.5v1.5Zm1.2-4.4-.7.5a1.3 1.3 0 0 0-.4 1v.5H7.8V9a2 2 0 0 1 .8-1.6l.6-.5a1.2 1.2 0 0 0 .4-1 1.6 1.6 0 0 0-3.2 0H5a3 3 0 0 1 6 0 2.4 2.4 0 0 1-1.1 2Z" />
    </svg>
);

const LogoutIcon = (props: React.SVGAttributes<SVGElement>) => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" {...props}>
        <path d="M6.5 2h-3A1.5 1.5 0 0 0 2 3.5v9A1.5 1.5 0 0 0 3.5 14h3v-1.5h-3v-9h3V2Zm4.6 3.2L9.9 6.4l1.4 1.4H6v1.5h5.3l-1.4 1.4 1.2 1.1L14 7.9l-2.9-2.7Z" />
    </svg>
);

/* ==================== TYPES ==================== */

interface SpaceItem {
    id: string;
    label: string;
    Icon: React.ComponentType<React.SVGAttributes<SVGElement>>;
    url: string;
    badge?: number;
}

interface ModuleItem {
    id: string;
    label: string;
    url: string;
    badge?: number;
}

/* Configuration des espaces (colonne 68px, comme Element Web) */
const SPACES: SpaceItem[] = [
    { id: "home", label: "Accueil", Icon: HomeIcon, url: "/" },
    { id: "drive", label: "Fichiers", Icon: FolderIcon, url: "/drive/" },
    { id: "chat", label: "Discussions", Icon: ChatIcon, url: "/chat/", badge: 3 },
    { id: "meet", label: "Reunions", Icon: VideoIcon, url: "/meet/" },
];

/* Modules de l'espace actif (dans le LeftPanel) */
const MODULES: ModuleItem[] = [
    { id: "transfers", label: "Transferts", url: "/transfers/", badge: 2 },
    { id: "projects", label: "Projets", url: "/projects/" },
    { id: "chat", label: "Discussions", url: "/chat/", badge: 3 },
    { id: "meet", label: "Reunions", url: "/meet/" },
];

/* ==================== SPACE PANEL (68px, comme Element Web) ==================== */

function SpacePanel({ activeId, onSelect }: { activeId: string; onSelect: (id: string) => void }) {
    return (
        <nav className="ls_SpacePanel" aria-label="Espaces">
            <ul>
                {SPACES.map(({ id, label, Icon, url, badge }) => (
                    <li key={id}>
                        <Tooltip label={label} placement="right">
                            <button
                                type="button"
                                className="ls_SpaceItem"
                                data-active={id === activeId}
                                aria-label={label}
                                onClick={() => onSelect(id)}
                            >
                                {badge ? <span className="ls_SpaceBadge">{badge}</span> : null}
                                <Icon />
                            </button>
                        </Tooltip>
                    </li>
                ))}
            </ul>
            <div className="ls_SpacePanel_footer">
                <Avatar id="user" name="Demo User" size="28px" />
            </div>
        </nav>
    );
}

/* ==================== LEFT PANEL (colonne principale, comme Element Web) ==================== */

function LeftPanel({ activeModuleId, onSelectModule }: { activeModuleId: string; onSelectModule: (id: string) => void }) {
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    return (
        <div className="ls_LeftPanel">
            {/* Recherche (comme RoomListSearch d'Element Web) */}
            <div className="ls_LeftPanel_header">
                <Search name="module-search" placeholder="Rechercher" />
            </div>

            {/* Liste des modules (comme RoomListView) */}
            <div className="ls_ModuleList" role="list">
                {MODULES.map((mod) => (
                    <button
                        key={mod.id}
                        type="button"
                        className="ls_ModuleItem"
                        data-active={mod.id === activeModuleId}
                        role="listitem"
                        onClick={() => onSelectModule(mod.id)}
                    >
                        <span className="ls_ModuleLabel">{mod.label}</span>
                        {mod.badge ? <Badge count={mod.badge} /> : null}
                    </button>
                ))}
            </div>

            <Separator horizontal className="ls_UserSeparator" />

            {/* Menu utilisateur en bas (comme Element Web UserMenu) */}
            <div className="ls_UserMenu">
                <button
                    type="button"
                    className="ls_UserMenuButton"
                    aria-expanded={userMenuOpen}
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                    <Avatar id="demo" name="Demo User" size="32px" />
                    <span className="ls_UserInfo">
                        <span className="ls_UserName">Demo User</span>
                        <span className="ls_UserEmail">demo@lastarter.local</span>
                    </span>
                </button>

                {userMenuOpen && (
                    <div className="ls_UserMenuDropdown" role="menu">
                        <button type="button" className="ls_MenuItem" role="menuitem">
                            <SettingsIcon /> Parametres
                        </button>
                        <button type="button" className="ls_MenuItem" role="menuitem">
                            <HelpIcon /> Aide
                        </button>
                        <Separator horizontal />
                        <button type="button" className="ls_MenuItem ls_MenuItemDanger" role="menuitem">
                            <LogoutIcon /> Se deconnecter
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ==================== CONTENU PRINCIPAL ==================== */

function MainContent({ activeModuleId }: { activeModuleId: string }) {
    const activeModule = MODULES.find((m) => m.id === activeModuleId) ?? MODULES[0];

    return (
        <main className="ls_MainContent">
            <header className="ls_PageHeader">
                <Body as="h1" size="lg" weight="medium">
                    {activeModule.label}
                </Body>
                <TextButton>Nouveau</TextButton>
            </header>

            <div className="ls_PageBody">
                <Body size="md" className="ls_Placeholder">
                    Module {activeModule.label} : contenu en cours d'integration.
                </Body>
            </div>
        </main>
    );
}

/* ==================== APP SHELL ==================== */

export function AppShell() {
    const [activeSpace, setActiveSpace] = useState("home");
    const [activeModule, setActiveModule] = useState("transfers");

    return (
        <div className="ls_AppShell">
            <SpacePanel activeId={activeSpace} onSelect={setActiveSpace} />
            <LeftPanel activeModuleId={activeModule} onSelectModule={setActiveModule} />
            <MainContent activeModuleId={activeModule} />
        </div>
    );
}
