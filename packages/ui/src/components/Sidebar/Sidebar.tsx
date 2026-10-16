/*
 * LaStarter UI : Sidebar double colonne (copie conforme Element Web).
 * SpacePanel (68px, icenes) + LeftPanel (260px, items + user menu).
 * Copyright 2026 LaStarter. Base sur Element Web LeftPanel + SpacePanel.
 */

import classNames from "classnames";
import React from "react";
import type { NavSection, Space, User } from "../../types";
import { getInitials } from "../../utils";
import { Avatar } from "../Avatar/Avatar";
import styles from "./Sidebar.module.css";

/* Icone recherche SVG */
function SearchIcon() {
    return (
        <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <path
                d="M7 12A5 5 0 1 0 7 2a5 5 0 0 0 0 10Zm4.5-1L14 13.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
            />
        </svg>
    );
}

/* Icone parametres SVG */
function SettingsIcon() {
    return (
        <svg
            width="18"
            height="18"
            viewBox="0 0 18 18"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
        >
            <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.5" />
            <path
                d="M9 1.5v2M9 14.5v2M1.5 9h2M14.5 9h2M3.8 3.8l1.4 1.4M12.8 12.8l1.4 1.4M14.2 3.8l-1.4 1.4M5.2 12.8l-1.4 1.4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
            />
        </svg>
    );
}

export interface SidebarProps {
    /** Espaces de 1er niveau (SpacePanel). */
    spaces: Space[];
    /** ID de l'espace actif. */
    activeSpaceId?: string;
    /** Callback clic sur un espace. */
    onSpaceClick?: (space: Space) => void;
    /** Callback clic sur le bouton + (creer un espace). */
    onSpaceCreate?: () => void;

    /** Placeholder recherche. */
    searchPlaceholder?: string;
    /** Callback clic recherche. */
    onSearchClick?: () => void;

    /** Sections de 2eme niveau (LeftPanel). */
    sections: NavSection[];

    /** Utilisateur connecte (UserMenu en bas). */
    user: User;
    /** Callback clic parametres. */
    onSettingsClick?: () => void;
    /** Callback clic profil utilisateur. */
    onUserClick?: () => void;
}

export function Sidebar({
    spaces,
    activeSpaceId,
    onSpaceClick,
    onSpaceCreate,
    searchPlaceholder = "Rechercher",
    onSearchClick,
    sections,
    user,
    onSettingsClick,
    onUserClick,
}: SidebarProps) {
    return (
        <>
            {/* 1ere colonne : SpacePanel (68px) */}
            <nav className={styles.spacePanel} aria-label="Espaces">
                {spaces.map((space) => (
                    <button
                        key={space.id}
                        type="button"
                        className={classNames(styles.spaceItem)}
                        data-active={space.id === activeSpaceId}
                        onClick={() => onSpaceClick?.(space)}
                        aria-label={space.label}
                        title={space.label}
                    >
                        {space.icon ?? getInitials(space.label)}
                        {space.unreadCount !== undefined && space.unreadCount > 0 && (
                            <span className={styles.spaceItemBadge}>{space.unreadCount}</span>
                        )}
                    </button>
                ))}
                {onSpaceCreate && (
                    <button
                        type="button"
                        className={styles.spaceAddButton}
                        onClick={onSpaceCreate}
                        aria-label="Ajouter un espace"
                        title="Ajouter un espace"
                    >
                        +
                    </button>
                )}
            </nav>

            {/* 2eme colonne : LeftPanel (260px) */}
            <aside className={styles.leftPanel}>
                {onSearchClick && (
                    <button
                        type="button"
                        className={styles.leftPanelSearch}
                        onClick={onSearchClick}
                    >
                        <SearchIcon />
                        <span>{searchPlaceholder}</span>
                    </button>
                )}

                <nav className={styles.leftPanelNav} aria-label="Navigation">
                    {sections.map((section) => (
                        <React.Fragment key={section.id}>
                            {section.title && (
                                <div className={styles.leftPanelSection}>{section.title}</div>
                            )}
                            {section.items.map((item) => (
                                <button
                                    key={item.id}
                                    type="button"
                                    className={styles.leftPanelItem}
                                    data-active={item.active}
                                    onClick={
                                        item.onClick ??
                                        (() => {
                                            if (item.href) {
                                                window.location.href = item.href;
                                            }
                                        })
                                    }
                                >
                                    {item.icon && (
                                        <span className={styles.leftPanelItemIcon}>
                                            {item.icon}
                                        </span>
                                    )}
                                    <span className={styles.leftPanelItemLabel}>{item.label}</span>
                                    {item.unreadCount !== undefined && item.unreadCount > 0 && (
                                        <span className={styles.leftPanelItemBadge}>
                                            {item.unreadCount}
                                        </span>
                                    )}
                                </button>
                            ))}
                        </React.Fragment>
                    ))}
                </nav>

                {/* UserMenu en bas (copie Element Web) */}
                <div className={styles.userMenu}>
                    <button type="button" className={styles.userMenuButton} onClick={onUserClick}>
                        <Avatar name={user.displayName} src={user.avatarUrl} size="md" />
                        <span className={styles.userMenuInfo}>
                            <span className={styles.userMenuName}>{user.displayName}</span>
                            <span className={styles.userMenuEmail}>{user.email}</span>
                        </span>
                    </button>
                    {onSettingsClick && (
                        <button
                            type="button"
                            className={styles.userMenuSettings}
                            onClick={onSettingsClick}
                            aria-label="Parametres"
                        >
                            <SettingsIcon />
                        </button>
                    )}
                </div>
            </aside>
        </>
    );
}
