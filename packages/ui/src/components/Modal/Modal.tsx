/*
 * LaStarter UI : Modal avec createPortal (cf. Grafikart "Les portails").
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useEffect, useCallback } from "react";
import { createPortal } from "react-dom";
import styles from "./Modal.module.css";

export interface ModalProps {
    open: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
    closeOnOverlayClick?: boolean;
    closeOnEscape?: boolean;
}

export function Modal({
    open,
    onClose,
    title,
    children,
    closeOnOverlayClick = true,
    closeOnEscape = true,
}: ModalProps) {
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (closeOnEscape && e.key === "Escape") onClose();
        },
        [closeOnEscape, onClose],
    );

    useEffect(() => {
        if (!open) return;
        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [open, handleKeyDown]);

    if (!open) return null;

    return createPortal(
        <div
            className={styles.overlay}
            onClick={closeOnOverlayClick ? onClose : undefined}
            role="dialog"
            aria-modal="true"
            aria-label={title}
        >
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                {title && (
                    <div className={styles.header}>
                        <h2 className={styles.title}>{title}</h2>
                        <button type="button" className={styles.close} onClick={onClose} aria-label="Fermer">
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                        </button>
                    </div>
                )}
                <div className={styles.body}>{children}</div>
            </div>
        </div>,
        document.body,
    );
}
