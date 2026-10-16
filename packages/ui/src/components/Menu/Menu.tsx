import React from "react";
import styles from "./Menu.module.css";

export interface MenuItem { id: string; label: string; icon?: React.ReactNode; onClick?: () => void; active?: boolean; destructive?: boolean; separator?: boolean; }

export interface MenuProps { items: MenuItem[]; open: boolean; onClose: () => void; style?: React.CSSProperties; }

export function Menu({ items, open, onClose, style }: MenuProps) {
    if (!open) return null;
    return (
        <nav className={styles.menu} style={style} role="menu">
            {items.map((item) => item.separator ? <div key={item.id} className={styles.separator} /> : (
                <button key={item.id} type="button" className={`${styles.item} ${item.destructive ? styles.itemDestructive : ""}`} data-active={item.active} onClick={() => { item.onClick?.(); onClose(); }} role="menuitem">
                    {item.icon}{item.label}
                </button>
            ))}
        </nav>
    );
}