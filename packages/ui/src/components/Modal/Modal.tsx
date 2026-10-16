import React, { useEffect } from "react";
import styles from "./Modal.module.css";

export interface ModalProps { open: boolean; onClose: () => void; title?: string; children: React.ReactNode; }

export function Modal({ open, onClose, title, children }: ModalProps) {
    useEffect(() => { if (!open) return; const esc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); }; window.addEventListener("keydown", esc); return () => window.removeEventListener("keydown", esc); }, [open, onClose]);
    if (!open) return null;
    return (
        <div className={styles.overlay} onClick={onClose} role="dialog" aria-modal="true" aria-label={title}>
            <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                {title && <div className={styles.header}><h2 className={styles.title}>{title}</h2><button type="button" className={styles.close} onClick={onClose} aria-label="Fermer">x</button></div>}
                <div className={styles.body}>{children}</div>
            </div>
        </div>
    );
}