/*
 * LaStarter UI : Button (copie conforme Compound Web).
 * Copyright 2026 LaStarter. Base sur Compound (Element).
 */

import classNames from "classnames";
import type React from "react";
import { type ComponentType, type PropsWithChildren, forwardRef } from "react";
import type { ButtonKind, ComponentSize } from "../../types";
import styles from "./Button.module.css";

export interface ButtonProps extends PropsWithChildren {
    kind?: ButtonKind;
    size?: ComponentSize;
    Icon?: ComponentType<React.SVGAttributes<SVGElement>>;
    iconOnly?: boolean;
    destructive?: boolean;
    disabled?: boolean;
    href?: string;
    type?: "button" | "submit" | "reset";
    onClick?: (e: React.MouseEvent) => void;
    className?: string;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
    {
        kind = "primary",
        size = "md",
        children,
        className,
        iconOnly,
        Icon,
        destructive = false,
        disabled,
        href,
        type = "button",
        onClick,
        ...rest
    },
    ref,
) {
    const classes = classNames(styles.button, className, {
        [styles.hasIcon]: Icon,
        [styles.iconOnly]: iconOnly,
        [styles.destructive]: destructive,
    });
    const iconSize = iconOnly && size === "lg" ? 24 : 20;
    const content = (
        <>
            {Icon && <Icon width={iconSize} height={iconSize} aria-hidden={true} />}
            {children}
        </>
    );
    if (href) {
        return (
            <a
                ref={ref as never}
                href={href}
                className={classes}
                data-size={size}
                data-kind={kind}
                tabIndex={0}
                {...rest}
            >
                {content}
            </a>
        );
    }
    return (
        <button
            ref={ref}
            type={type}
            className={classes}
            data-size={size}
            data-kind={kind}
            tabIndex={0}
            disabled={disabled}
            onClick={onClick}
            {...rest}
        >
            {content}
        </button>
    );
});
