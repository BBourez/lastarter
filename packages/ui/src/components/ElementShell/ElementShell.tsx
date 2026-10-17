/*
 * LaStarter UI : ElementShell avec les VRAIS composants Compound.
 * Structure identique a Element Web : SpacePanel (68px) + LeftPanel (280px) + Main.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useState } from "react";
import {
    Avatar,
    Badge,
    Search,
    Separator,
    Tooltip,
} from "@vector-im/compound-web";
import "./element-shell.css";

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

export interface ShellSpace {
    id: string;
    label: string;
    Icon: React.ComponentType<React.SVGAttributes<SVGElement>>;
    url: string;
    badge?: number;
}

export interface ShellModule {
    id: string;
    label: string;
    url: string;
    badge?: number;
}

export interface ElementShellUser {
    displayName: string;
    email: string;
}

export interface ElementShellProps {
    /** Espaces affiches dans la colonne 68px (default : la barre standard LaStarter). */
    spaces?: ShellSpace[];
    /** Modules affiches dans le LeftPanel. */
    modules: ShellModule[];
    /** Id du module actif (surlignage). */
    activeModuleId: string;
    /** Utilisateur affiche en bas du LeftPanel. */
    user?: ElementShellUser;
    /** Contenu principal (droite). */
    children: React.ReactNode;
}

/* ==================== ESPACES PAR DEFAUT ==================== */

export const DEFAULT_SPACES: ShellSpace[] = [
    { id: "home", label: "Accueil", Icon: HomeIcon, url: "http://localhost/" },
    { id: "drive", label: "Fichiers", Icon: FolderIcon, url: "http://drive.localhost/" },
    { id: "chat", label: "Discussions", Icon: ChatIcon, url: "http://chat.localhost/", badge: 3 },
    { id: "meet", label: "Reunions", Icon: VideoIcon, url: "http://meet.localhost/" },
];

/* ==================== SPACE PANEL (68px, copie _SpacePanel.pcss) ==================== */

function SpacePanel({ spaces, activeId }: { spaces: ShellSpace[]; activeId: string }) {
    return (
        <nav className="ls_SpacePanel" aria-label="Espaces">
            <ul>
                {spaces.map(({ id, label, Icon, url, badge }) => (
                    <li key={id}>
                        <Tooltip label={label} placement="right">
                            <a
                                className="ls_SpaceItem"
                                href={url}
                                data-active={id === activeId}
                                aria-label={label}
                            >
                                {badge ? <span className="ls_SpaceBadge">{badge}</span> : null}
                                <Icon />
                            </a>
                        </Tooltip>
                    </li>
                ))}
            </ul>
            <div className="ls_SpacePanel_footer">
                <Avatar id="user" name="LaStarter" size="28px" />
            </div>
        </nav>
    );
}

/* ==================== LEFT PANEL (comme _LeftPanel.pcss) ==================== */

function LeftPanel({
    modules,
    activeModuleId,
    user,
}: {
    modules: ShellModule[];
    activeModuleId: string;
    user: ElementShellUser;
}) {
    const [userMenuOpen, setUserMenuOpen] = useState(false);

    return (
        <div className="ls_LeftPanel">
            <div className="ls_LeftPanel_header">
                <Search name="module-search" placeholder="Rechercher" />
            </div>

            <div className="ls_ModuleList" role="list">
                {modules.map((mod) => (
                    <a
                        key={mod.id}
                        className="ls_ModuleItem"
                        href={mod.url}
                        data-active={mod.id === activeModuleId}
                        role="listitem"
                    >
                        <span className="ls_ModuleLabel">{mod.label}</span>
                        {mod.badge ? <Badge count={mod.badge} /> : null}
                    </a>
                ))}
            </div>

            <Separator horizontal className="ls_UserSeparator" />

            <div className="ls_UserMenu">
                <button
                    type="button"
                    className="ls_UserMenuButton"
                    aria-expanded={userMenuOpen}
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                    <Avatar id="demo" name={user.displayName} size="32px" />
                    <span className="ls_UserInfo">
                        <span className="ls_UserName">{user.displayName}</span>
                        <span className="ls_UserEmail">{user.email}</span>
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

/* ==================== ELEMENT SHELL ==================== */

export function ElementShell({
    spaces = DEFAULT_SPACES,
    modules,
    activeModuleId,
    user = { displayName: "Demo User", email: "demo@lastarter.local" },
    children,
}: ElementShellProps) {
    return (
        <div className="ls_AppShell">
            <SpacePanel spaces={spaces} activeId="home" />
            <LeftPanel modules={modules} activeModuleId={activeModuleId} user={user} />
            <main className="ls_MainContent">{children}</main>
        </div>
    );
}
