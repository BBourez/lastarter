/*
 * LaStarter UI : Toast (notifications empilables, createPortal).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import type { AlertVariant } from "../Alert/Alert";
import styles from "./Toast.module.css";

export interface ToastData {
    id: string;
    message: string;
    variant?: AlertVariant;
    /** Duree en ms avant disparition (0 = manuel). */
    duration?: number;
}

export interface ToastProps {
    toasts: ToastData[];
    onDismiss: (id: string) => void;
}

const variantIcons: Record<AlertVariant, string> = {
    success: "OK",
    error: "X",
    warning: "!",
    info: "i",
};

function ToastItem({ toast, onDismiss }: { toast: ToastData; onDismiss: (id: string) => void }) {
    const dismiss = useCallback(() => onDismiss(toast.id), [onDismiss, toast.id]);

    useEffect(() => {
        if (toast.duration && toast.duration > 0) {
            const timer = setTimeout(dismiss, toast.duration);
            return () => clearTimeout(timer);
        }
        return undefined;
    }, [dismiss, toast.duration]);

    return (
        <div className={styles.toast} data-variant={toast.variant ?? "info"} role="status">
            <span className={styles.icon}>{variantIcons[toast.variant ?? "info"]}</span>
            <span className={styles.message}>{toast.message}</span>
            <button type="button" className={styles.close} onClick={dismiss} aria-label="Fermer">
                x
            </button>
        </div>
    );
}

export function Toast({ toasts, onDismiss }: ToastProps) {
    if (toasts.length === 0) return null;

    return createPortal(
        <div className={styles.container} aria-live="polite">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
            ))}
        </div>,
        document.body,
    );
}
