/*
 * LaStarter UI : Tabs (navigation par onglets avec underline Compound).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import type React from "react";
import { useCallback, useState } from "react";
import styles from "./Tabs.module.css";

export interface TabItem {
    id: string;
    label: string;
    icon?: React.ReactNode;
    disabled?: boolean;
}

export interface TabsProps {
    items: TabItem[];
    activeId: string;
    onChange: (id: string) => void;
    /** Aria-label pour l'accessibilite. */
    ariaLabel?: string;
}

export function Tabs({ items, activeId, onChange, ariaLabel }: TabsProps) {
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent, index: number) => {
            if (e.key === "ArrowRight") {
                e.preventDefault();
                const next = items[index + 1];
                if (next && !next.disabled) onChange(next.id);
            } else if (e.key === "ArrowLeft") {
                e.preventDefault();
                const prev = items[index - 1];
                if (prev && !prev.disabled) onChange(prev.id);
            }
        },
        [items, onChange],
    );

    return (
        <div className={styles.tabs} role="tablist" aria-label={ariaLabel}>
            {items.map((item, index) => (
                <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={item.id === activeId}
                    aria-disabled={item.disabled}
                    tabIndex={item.id === activeId ? 0 : -1}
                    className={styles.tab}
                    data-active={item.id === activeId}
                    data-disabled={item.disabled}
                    onClick={() => !item.disabled && onChange(item.id)}
                    onKeyDown={(e) => handleKeyDown(e, index)}
                >
                    {item.icon}
                    <span>{item.label}</span>
                </button>
            ))}
        </div>
    );
}
