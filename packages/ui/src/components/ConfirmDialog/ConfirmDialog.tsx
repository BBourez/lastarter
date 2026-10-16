/*
 * LaStarter UI : ConfirmDialog (pattern callable, cf. Grafikart "react-call").
 * Appelable avec await : const confirmed = await ConfirmDialog.call({ title: "..." })
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { Button } from "../Button/Button";
import { Modal } from "../Modal/Modal";

/* ==================== TYPES ==================== */

export interface ConfirmDialogOptions {
    title?: string;
    message?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    destructive?: boolean;
}

type Resolver = (value: boolean) => void;

interface PendingCall {
    options: ConfirmDialogOptions;
    resolve: Resolver;
}

/* ==================== ETAT GLOBAL (singleton pattern) ==================== */

let pendingCall: PendingCall | null = null;
const listeners = new Set<() => void>();

/** Notifier tous les listeners qu'un appel est en attente ou resolu. */
function notify(): void {
    for (const listener of listeners) {
        listener();
    }
}

/** S'abonner aux changements d'etat du ConfirmDialog. */
function subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
}

/** Obtenir l'appel en cours. */
function getSnapshot(): PendingCall | null {
    return pendingCall;
}

/* ==================== API PUBLIQUE (callable) ==================== */

export const ConfirmDialog = {
    /**
     * Afficher un dialog de confirmation et attendre la reponse.
     * @example
     * const confirmed = await ConfirmDialog.call({ title: "Supprimer ?" });
     * if (confirmed) { /* supprimer *\/ }
     */
    call(options: ConfirmDialogOptions = {}): Promise<boolean> {
        return new Promise<boolean>((resolve) => {
            pendingCall = { options, resolve };
            notify();
        });
    },

    /** Nom d'affichage pour React DevTools. */
    displayName: "ConfirmDialog",
};

/* ==================== COMPOSANT (a monter dans l'app) ==================== */

/** Hook interne pour suivre l'etat du pendingCall. */
function usePendingCall(): PendingCall | null {
    const [call, setCall] = useState<PendingCall | null>(getSnapshot());

    useEffect(() => {
        return subscribe(() => setCall(getSnapshot()));
    }, []);

    return call;
}

/**
 * Racine du ConfirmDialog. A monter une fois dans l'application :
 * <ConfirmDialogRoot />
 */
export function ConfirmDialogRoot() {
    const call = usePendingCall();

    const handleConfirm = useCallback(() => {
        if (call) {
            call.resolve(true);
            pendingCall = null;
            notify();
        }
    }, [call]);

    const handleCancel = useCallback(() => {
        if (call) {
            call.resolve(false);
            pendingCall = null;
            notify();
        }
    }, [call]);

    if (!call) return null;

    const { options } = call;

    return createPortal(
        <div
            style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0,0,0,0.4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 2000,
            }}
            role="alertdialog"
            aria-modal="true"
            aria-label={options.title ?? "Confirmation"}
        >
            <div
                style={{
                    background: "var(--ls-color-bg, #fff)",
                    borderRadius: "var(--ls-radius-md, 8px)",
                    border: "1px solid var(--ls-color-border, #e1e6ec)",
                    padding: "24px",
                    maxWidth: 400,
                    width: "90%",
                    fontFamily: "var(--ls-font-family, Inter, sans-serif)",
                }}
            >
                {options.title && (
                    <h2
                        style={{
                            fontSize: "var(--ls-font-size-h3, 20px)",
                            fontWeight: 600,
                            color: "var(--ls-color-text, #1b1d22)",
                            margin: "0 0 12px",
                        }}
                    >
                        {options.title}
                    </h2>
                )}
                {options.message && (
                    <p
                        style={{
                            fontSize: "var(--ls-font-size-md, 15px)",
                            color: "var(--ls-color-text-secondary, #656d77)",
                            lineHeight: 1.5,
                            margin: "0 0 20px",
                        }}
                    >
                        {options.message}
                    </p>
                )}
                <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                    <Button kind="secondary" onClick={handleCancel}>
                        {options.cancelLabel ?? "Annuler"}
                    </Button>
                    <Button
                        kind={options.destructive ? "primary" : "accent"}
                        destructive={options.destructive}
                        onClick={handleConfirm}
                    >
                        {options.confirmLabel ?? "Confirmer"}
                    </Button>
                </div>
            </div>
        </div>,
        document.body,
    );
}
