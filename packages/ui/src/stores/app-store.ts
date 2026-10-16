/*
 * LaStarter UI : store Zustand partage (cf. Grafikart "Zustand").
 * Etat global de l'application : utilisateur, theme, modules actifs.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "../types";

/* ==================== TYPES ==================== */

export type ThemeMode = "light" | "dark" | "system";

export interface ActiveModule {
    id: string;
    label: string;
    url: string;
    icon?: string;
}

interface AppState {
    /* Utilisateur connecte */
    user: User | null;
    setUser: (user: User | null) => void;

    /* Theme visuel */
    theme: ThemeMode;
    setTheme: (theme: ThemeMode) => void;

    /* Langue active */
    locale: string;
    setLocale: (locale: string) => void;

    /* Modules actifs (portes depuis le CLI) */
    modules: ActiveModule[];
    setModules: (modules: ActiveModule[]) => void;

    /* Module actuellement ouvert */
    activeModuleId: string | null;
    setActiveModule: (id: string | null) => void;

    /* Sidebar : espace actif */
    activeSpaceId: string | null;
    setActiveSpace: (id: string | null) => void;

    /* Sidebar : repliee ou non */
    sidebarCollapsed: boolean;
    toggleSidebar: () => void;
}

/* ==================== STORE ==================== */

export const useAppStore = create<AppState>()(
    persist(
        (set) => ({
            user: null,
            setUser: (user) => set({ user }),

            theme: "system",
            setTheme: (theme) => set({ theme }),

            locale: "fr",
            setLocale: (locale) => set({ locale }),

            modules: [],
            setModules: (modules) => set({ modules }),

            activeModuleId: null,
            setActiveModule: (id) => set({ activeModuleId: id }),

            activeSpaceId: null,
            setActiveSpace: (id) => set({ activeSpaceId: id }),

            sidebarCollapsed: false,
            toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
        }),
        {
            name: "lastarter-app",
            partialize: (state) => ({
                theme: state.theme,
                locale: state.locale,
                sidebarCollapsed: state.sidebarCollapsed,
            }),
        },
    ),
);

/* ==================== SELECTEURS (cf. Grafikart Zustand) ==================== */

/** Recuperer uniquement l'utilisateur (optimise les re-rendus). */
export const useCurrentUser = () => useAppStore((state) => state.user);

/** Recuperer uniquement le theme. */
export const useTheme = () => useAppStore((state) => state.theme);

/** Recuperer uniquement la langue. */
export const useLocale = () => useAppStore((state) => state.locale);

/** Recuperer les modules actifs. */
export const useModules = () => useAppStore((state) => state.modules);

/** Verifier si l'utilisateur est connecte. */
export const useIsAuthenticated = () => useAppStore((state) => state.user !== null);

/* ==================== ACTIONS HORS STORE (cf. Grafikart) ==================== */

/** Deconnexion : reinitialiser l'utilisateur. */
export function logout(): void {
    useAppStore.getState().setUser(null);
}

/** Recuperer le module actif. */
export function getActiveModule(): ActiveModule | null {
    const { modules, activeModuleId } = useAppStore.getState();
    return modules.find((m) => m.id === activeModuleId) ?? null;
}
