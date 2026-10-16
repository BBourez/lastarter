/*
 * LaStarter UI — Sidebar (copie conforme Element Web LeftPanel).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: AGPL-3.0-only.
 * Structure : Search (pilule) → Items scrollables → UserMenu (avatar + nom + email + settings).
 */

import React from "react";
import classNames from "classnames";
import styles from "./Sidebar.module.css";

/* ================================================================
 * TYPES
 * ================================================================ */

export interface SidebarUser {
    /** Nom complet affiché (ex: "Jean Dupont") */
    displayName: string;
    /** Email affiché sous le nom */
    email: string;
    /** URL de l'avatar (optionnel — sinon initiales) */
    avatarUrl?: string;
}

export interface SidebarItem {
    /** Icône (emoji ou composant React) */
    icon?: React.ReactNode;
    /** Libellé de l'item */
    label: string;
    /** URL ou callback au clic */
    href?: string;
    onClick?: () => void;
    /** Item actif (fond vert subtil) */
    active?: boolean;
    /** Badge numérique (ex: nombre de non-lus) */
    badge?: number;
}

export interface SidebarSection {
    /** Titre de la section (ex: "Fichiers", "Favoris") */
    title?: string;
    /** Items de cette section */
    items: SidebarItem[];
}

export interface SidebarProps {
    /** Placeholder de la recherche */
    searchPlaceholder?: string;
    /** Callback au clic sur la recherche */
    onSearchClick?: () => void;
    /** Icône de recherche (défaut : loupe SVG) */
    searchIcon?: React.ReactNode;
    /** Sections d'items (chaque section peut avoir un titre) */
    sections: SidebarSection[];
    /** Infos utilisateur pour le menu en bas */
    user: SidebarUser;
    /** Callback au clic sur paramètres */
    onSettingsClick?: () => void;
    /** Callback au clic sur l'utilisateur (dropdown profil) */
    onUserClick?: () => void;
}

/* ================================================================
 * ICÔNES (SVG inline — pas de dépendance externe)
 * ================================================================ */

const DefaultSearchIcon = () => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path
            d="M7 12A5 5 0 1 0 7 2a5 5 0 0 0 0 10Zm4.5-1L14 13.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
        />
    </svg>
);

const DefaultSettingsIcon = () => (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.5" />
        <path
            d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.8 3.8l1.4 1.4M12.8 12.8l1.4 1.4M14.2 3.8l-1.4 1.4M5.2 12.8l-1.4 1.4"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
        />
    </svg>
);

/* ================================================================
 * SOUS-COMPOSANTS
 * ================================================================ */

function SidebarItemLink({ item }: { item: SidebarItem }) {
    const cls = classNames(styles.sidebar__item, {
        [styles["sidebar__item--active"]]: item.active,
    });

    const content = (
        <>
            {item.icon && <span className={styles.sidebar__itemIcon}>{item.icon}</span>}
            <span className={styles.sidebar__itemLabel}>{item.label}</span>
            {item.badge !== undefined && (
                <span className={styles.sidebar__itemBadge}>{item.badge}</span>
            )}
        </>
    );

    if (item.href) {
        return (
            <a href={item.href} className={cls}>
                {content}
            </a>
        );
    }
    return (
        <button type="button" className={cls} onClick={item.onClick}>
            {content}
        </button>
    );
}

function UserMenu({
    user,
    onSettingsClick,
    onUserClick,
}: {
    user: SidebarUser;
    onSettingsClick?: () => void;
    onUserClick?: () => void;
}) {
    const initials = user.displayName
        .split(" ")
        .map((w) => w[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();

    return (
        <div className={styles.sidebar__user}>
            <button type="button" className={styles.sidebar__userButton} onClick={onUserClick}>
                <span className={styles.sidebar__userAvatar}>
                    {user.avatarUrl ? (
                        <img src={user.avatarUrl} alt={user.displayName} />
                    ) : (
                        initials
                    )}
                </span>
                <span className={styles.sidebar__userInfo}>
                    <span className={styles.sidebar__userName}>{user.displayName}</span>
                    <span className={styles.sidebar__userEmail}>{user.email}</span>
                </span>
            </button>
            {onSettingsClick && (
                <button
                    type="button"
                    className={styles.sidebar__userSettings}
                    onClick={onSettingsClick}
                    aria-label="Paramètres"
                >
                    <DefaultSettingsIcon />
                </button>
            )}
        </div>
    );
}

/* ================================================================
 * SIDEBAR (composant principal)
 * ================================================================ */

export function Sidebar({
    searchPlaceholder = "Rechercher…",
    onSearchClick,
    searchIcon,
    sections,
    user,
    onSettingsClick,
    onUserClick,
}: SidebarProps) {
    return (
        <aside className={styles.sidebar}>
            {onSearchClick && (
                <button
                    type="button"
                    className={styles.sidebar__search}
                    onClick={onSearchClick}
                >
                    {searchIcon || <DefaultSearchIcon />}
                    <span>{searchPlaceholder}</span>
                </button>
            )}

            <nav className={styles.sidebar__nav}>
                {sections.map((section, i) => (
                    <React.Fragment key={i}>
                        {section.title && (
                            <div className={styles.sidebar__section}>{section.title}</div>
                        )}
                        {section.items.map((item, j) => (
                            <SidebarItemLink key={j} item={item} />
                        ))}
                    </React.Fragment>
                ))}
            </nav>

            <UserMenu user={user} onSettingsClick={onSettingsClick} onUserClick={onUserClick} />
        </aside>
    );
}
