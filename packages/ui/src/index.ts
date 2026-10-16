/*
 * LaStarter UI : exports publics.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Tokens (importer une fois dans l'app hote) */
import "./tokens.css";

/* Types */
export type {
    User,
    Space,
    NavItem,
    NavSection,
    ButtonKind,
    ComponentSize,
    Direction,
    AsyncState,
} from "./types";

/* Utils */
export { cn, getInitials, formatFileSize, debounce, isDefined } from "./utils";

/* Composants */
export { Button } from "./components/Button/Button";
export type { ButtonProps } from "./components/Button/Button";

export { Input } from "./components/Input/Input";
export type { InputProps } from "./components/Input/Input";

export { Badge } from "./components/Badge/Badge";
export type { BadgeProps, BadgeVariant } from "./components/Badge/Badge";

export { Avatar } from "./components/Avatar/Avatar";
export type { AvatarProps } from "./components/Avatar/Avatar";

export { Separator } from "./components/Separator/Separator";

export { Sidebar } from "./components/Sidebar/Sidebar";
export type { SidebarProps } from "./components/Sidebar/Sidebar";

export { Modal } from "./components/Modal/Modal";
export type { ModalProps } from "./components/Modal/Modal";

export { Menu } from "./components/Menu/Menu";
export type { MenuProps, MenuItem } from "./components/Menu/Menu";

export { Switch } from "./components/Switch/Switch";
export type { SwitchProps } from "./components/Switch/Switch";

export { Alert } from "./components/Alert/Alert";
export type { AlertProps, AlertVariant } from "./components/Alert/Alert";

/* Hooks personnalises (cf. Grafikart) */
export {
    useToggle,
    useClickOutside,
    useMediaQuery,
    useDocumentTitle,
    useDebouncedValue,
} from "./hooks";

/* Store Zustand (cf. Grafikart) */
export { useAppStore, useCurrentUser, useTheme, useLocale, useModules, useIsAuthenticated, logout, getActiveModule } from "./stores/app-store";
export type { ThemeMode, ActiveModule } from "./stores/app-store";

/* Slot (pattern asChild, cf. Grafikart) */
export { Slot } from "./components/Slot/Slot";
export type { AsChildProps } from "./components/Slot/Slot";

/* ConfirmDialog (pattern callable, cf. Grafikart react-call) */
export { ConfirmDialog, ConfirmDialogRoot } from "./components/ConfirmDialog/ConfirmDialog";
export type { ConfirmDialogOptions } from "./components/ConfirmDialog/ConfirmDialog";
