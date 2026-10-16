/*
 * Tests du store Zustand.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { logout, useAppStore, useCurrentUser, useIsAuthenticated } from "./app-store";

describe("useAppStore", () => {
    beforeEach(() => {
        // Reinitialiser le store avant chaque test
        useAppStore.setState({ user: null, theme: "system", locale: "fr" });
    });

    it("initialise avec user=null", () => {
        const { result } = renderHook(() => useCurrentUser());
        expect(result.current).toBeNull();
    });

    it("setUser met a jour l'utilisateur", () => {
        const { result } = renderHook(() => useAppStore());
        const user = { id: "1", displayName: "Jean", email: "jean@test.com" };
        act(() => result.current.setUser(user));
        expect(result.current.user).toEqual(user);
    });

    it("useIsAuthenticated retourne false sans utilisateur", () => {
        const { result } = renderHook(() => useIsAuthenticated());
        expect(result.current).toBe(false);
    });

    it("useIsAuthenticated retourne true avec utilisateur", () => {
        const { result } = renderHook(() => useAppStore());
        act(() => result.current.setUser({ id: "1", displayName: "J", email: "j@t.com" }));
        const { result: authResult } = renderHook(() => useIsAuthenticated());
        expect(authResult.current).toBe(true);
    });

    it("logout remet user a null", () => {
        const { result } = renderHook(() => useAppStore());
        act(() => result.current.setUser({ id: "1", displayName: "J", email: "j@t.com" }));
        act(() => logout());
        expect(useAppStore.getState().user).toBeNull();
    });

    it("setTheme change le theme", () => {
        const { result } = renderHook(() => useAppStore());
        act(() => result.current.setTheme("dark"));
        expect(result.current.theme).toBe("dark");
    });

    it("setLocale change la langue", () => {
        const { result } = renderHook(() => useAppStore());
        act(() => result.current.setLocale("en"));
        expect(result.current.locale).toBe("en");
    });

    it("toggleSidebar inverse l'etat", () => {
        const { result } = renderHook(() => useAppStore());
        const initial = result.current.sidebarCollapsed;
        act(() => result.current.toggleSidebar());
        expect(result.current.sidebarCollapsed).toBe(!initial);
    });
});
