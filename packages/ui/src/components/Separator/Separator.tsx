import React from "react";
import styles from "./Separator.module.css";

export function Separator({
    orientation = "horizontal",
}: { orientation?: "horizontal" | "vertical" }) {
    return <div className={styles.separator} data-orientation={orientation} role="separator" />;
}
