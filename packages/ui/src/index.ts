/*
 * LaStarter UI — exports publics.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: AGPL-3.0-only.
 */

/* Tokens + fonts (à importer une fois dans l'app hôte) */
import "./tokens.css";
import "./fonts.css";

/* Sidebar (copie conforme Element Web) */
export { Sidebar } from "./components/Sidebar/Sidebar";
export type {
    SidebarProps,
    SidebarUser,
    SidebarItem,
    SidebarSection,
} from "./components/Sidebar/Sidebar";

/* Button (copie conforme Compound Web) */
export { Button } from "./components/Button/Button";
export type { ButtonProps, ButtonKind, ButtonSize } from "./components/Button/Button";
