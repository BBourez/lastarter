/*
 * LaStarter UI — Shell : wrapper d'application avec sidebar Element Web.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: AGPL-3.0-only.
 *
 * Le shell enveloppe le contenu d'une app existante :
 *   - Sidebar gauche (fond blanc, 260px, user menu en bas)
 *   - Pas de header — la sidebar EST la navigation
 *   - Le contenu de l'app est décalé à droite
 *   - Les sidebar/header natifs de l'app sont masqués via CSS
 */

import React, { useState, useEffect } from "react";
import { Sidebar, type SidebarUser, type SidebarSection } from "../Sidebar/Sidebar";
import "./LaStarterShell.css";

export interface LaStarterShellProps {
    /** Nom de l'app (affiché dans le breadcrumb/document.title) */
    appName: string;
    /** Sections de navigation pour la sidebar */
    navSections: SidebarSection[];
    /** Utilisateur courant (récupéré de l'API de l'app) */
    user: SidebarUser;
    /** Callback paramètres (ouvre la page settings de l'app) */
    onSettings?: () => void;
    /** Callback profil (dropdown utilisateur) */
    onUserProfile?: () => void;
    /** Placeholder de recherche */
    searchPlaceholder?: string;
    /** Callback recherche */
    onSearch?: () => void;
    /** Children = le contenu de l'app existante */
    children: React.ReactNode;
}

export function LaStarterShell({
    appName,
    navSections,
    user,
    onSettings,
    onUserProfile,
    searchPlaceholder,
    onSearch,
    children,
}: LaStarterShellProps) {
    // Titre de l'onglet
    useEffect(() => {
        document.title = `${appName} — ${user.displayName}`;
    }, [appName, user.displayName]);

    return (
        <div className="lastarter-shell">
            <Sidebar
                searchPlaceholder={searchPlaceholder ?? `Rechercher dans ${appName}…`}
                onSearchClick={onSearch}
                sections={navSections}
                user={user}
                onSettingsClick={onSettings}
                onUserClick={onUserProfile}
            />
            <main className="lastarter-shell__content">
                {children}
            </main>
        </div>
    );
}
