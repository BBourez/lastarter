import React from "react";
import { getInitials } from "../../utils";
import styles from "./Avatar.module.css";

export interface AvatarProps {
    name: string;
    src?: string;
    size?: "sm" | "md" | "lg";
    className?: string;
}

export function Avatar({ name, src, size = "md", className }: AvatarProps) {
    return (
        <span className={`${styles.avatar} ${className ?? ""}`} data-size={size}>
            {src ? <img src={src} alt={name} /> : getInitials(name)}
        </span>
    );
}
