/*
 * Tests des hooks personnalises.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useToggle, useDebouncedValue, useDocumentTitle, useMediaQuery } from "./index";

describe("useToggle", () => {
    it("initialise a false par defaut", () => {
        const { result } = renderHook(() => useToggle());
        expect(result.current[0]).toBe(false);
    });

    it("initialise a la valeur fournie", () => {
        const { result } = renderHook(() => useToggle(true));
        expect(result.current[0]).toBe(true);
    });

    it("toggle inverse la valeur", () => {
        const { result } = renderHook(() => useToggle(false));
        act(() => result.current[1]());
        expect(result.current[0]).toBe(true);
        act(() => result.current[1]());
        expect(result.current[0]).toBe(false);
    });

    it("setExplicit definit la valeur", () => {
        const { result } = renderHook(() => useToggle(false));
        act(() => result.current[2](true));
        expect(result.current[0]).toBe(true);
    });
});

describe("useDebouncedValue", () => {
    it("retourne la valeur initiale immediatement", () => {
        const { result } = renderHook(() => useDebouncedValue("init", 100));
        expect(result.current).toBe("init");
    });
});

describe("useDocumentTitle", () => {
    it("change le titre du document", () => {
        const original = document.title;
        const { rerender } = renderHook(({ title }) => useDocumentTitle(title), {
            initialProps: { title: "Nouveau titre" },
        });
        expect(document.title).toBe("Nouveau titre");
        rerender({ title: "Autre titre" });
        expect(document.title).toBe("Autre titre");
        document.title = original;
    });
});

describe("useMediaQuery", () => {
    it("retourne un booleen", () => {
        const { result } = renderHook(() => useMediaQuery("(min-width: 0px)"));
        expect(typeof result.current).toBe("boolean");
        expect(result.current).toBe(true);
    });
});
