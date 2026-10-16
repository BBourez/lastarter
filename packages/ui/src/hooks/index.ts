/*
 * LaStarter UI : hooks personnalises (cf. Grafikart "Creer un hook personnalise").
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { useState, useEffect, useRef, useCallback } from "react";

/* ==================== useToggle ==================== */

/**
 * Faire osciller une valeur entre vrai et faux.
 * @param initial Valeur initiale (defaut: false)
 * @returns [state, toggle, setExplicit]
 */
export function useToggle(initial = false): [boolean, () => void, (v: boolean) => void] {
    const [state, setState] = useState(initial);
    const toggle = useCallback(() => setState((v) => !v), []);
    return [state, toggle, setState];
}

/* ==================== useClickOutside ==================== */

/**
 * Detecter un clic en dehors d'un element (pour fermer menus/dropdowns).
 * @param handler Callback appele au clic exterieur
 * @returns Ref a attacher a l'element
 */
export function useClickOutside<T extends HTMLElement>(
    handler: () => void,
): React.RefObject<T | null> {
    const ref = useRef<T | null>(null);

    useEffect(() => {
        const listener = (event: MouseEvent | TouchEvent) => {
            const el = ref.current;
            if (!el || el.contains(event.target as Node)) return;
            handler();
        };
        document.addEventListener("mousedown", listener);
        document.addEventListener("touchstart", listener);
        return () => {
            document.removeEventListener("mousedown", listener);
            document.removeEventListener("touchstart", listener);
        };
    }, [handler]);

    return ref;
}

/* ==================== useMediaQuery ==================== */

/**
 * Detecter si une media query correspond (responsive).
 * @param query Media query CSS (ex: "(max-width: 768px)")
 * @returns true si la media query correspond
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(() =>
        typeof window !== "undefined" ? window.matchMedia(query).matches : false,
    );

    useEffect(() => {
        const mql = window.matchMedia(query);
        const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
        mql.addEventListener("change", handler);
        setMatches(mql.matches);
        return () => mql.removeEventListener("change", handler);
    }, [query]);

    return matches;
}

/* ==================== useDocumentTitle ==================== */

/**
 * Changer le titre de la page (restaure a l'unmount).
 * @param title Nouveau titre (null pour garder l'original)
 */
export function useDocumentTitle(title: string | null): void {
    const titleRef = useRef(document.title);

    useEffect(() => {
        return () => {
            document.title = titleRef.current ?? "";
        };
    }, []);

    useEffect(() => {
        document.title = title ?? titleRef.current ?? "";
    }, [title]);
}

/* ==================== useDebouncedValue ==================== */

/**
 * Debouncer une valeur (pour les champs de recherche).
 * @param value Valeur a debouncer
 * @param delayMs Delai en millisecondes (defaut: 300)
 * @returns Valeur debounced
 */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
    const [debounced, setDebounced] = useState(value);

    useEffect(() => {
        const timer = setTimeout(() => setDebounced(value), delayMs);
        return () => clearTimeout(timer);
    }, [value, delayMs]);

    return debounced;
}
