/*
 * LaStarter UI : types partages.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import type React from "react";

/** Utilisateur authentifie (recupere de l'API de l'app ou de Keycloak). */
export interface User {
    id: string;
    displayName: string;
    email: string;
    avatarUrl?: string;
}

/** Espace de premiere niveau (SpacePanel). */
export interface Space {
    id: string;
    label: string;
    icon?: React.ReactNode;
    /** Nombre d'elements non lus (badge). */
    unreadCount?: number;
}

/** Item de seconde niveau (LeftPanel / RoomList). */
export interface NavItem {
    id: string;
    label: string;
    icon?: React.ReactNode;
    href?: string;
    onClick?: () => void;
    active?: boolean;
    unreadCount?: number;
}

/** Groupe d'items dans la LeftPanel. */
export interface NavSection {
    id: string;
    title?: string;
    items: NavItem[];
}

/** Variante de bouton (specs Compound). */
export type ButtonKind = "primary" | "accent" | "secondary" | "tertiary" | "destructive";

/** Taille de composant (specs Compound). */
export type ComponentSize = "sm" | "md" | "lg";

/** Direction d'un separator ou layout. */
export type Direction = "horizontal" | "vertical";

/** Etat de chargement pour async. */
export type AsyncState = "idle" | "loading" | "success" | "error";
