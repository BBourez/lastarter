/*
 * LaStarter Portal : point d'entree de la suite.
 * Liste les modules actifs (depuis la config CLI).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Sidebar, type Space, type NavSection, type User } from "@lastarter/ui";
import { initI18n, useTranslation, detectLocale } from "@lastarter/i18n";
import { getEnv } from "@lastarter/config";

/* Configuration des modules actifs (generee par le CLI). */
interface ActiveModule {
    id: string;
    label: string;
    icon: string;
    url: string;
}

/* En attendant le CLI, config statique (sera remplacee par /portal-config.json). */
const MODULES: ActiveModule[] = [
    { id: "transfers", label: "Transferts", icon: "T", url: "/transfers/" },
    { id: "projects", label: "Projets", icon: "P", url: "/projects/" },
    { id: "chat", label: "Discussions", icon: "D", url: "/chat/" },
    { id: "meet", label: "Reunions", icon: "R", url: "/meet/" },
];

function Portal() {
    const { t } = useTranslation();
    const env = getEnv();
    const [activeModule, setActiveModule] = useState<string>("portal");

    /* Utilisateur de demo (sera remplace par l'API session). */
    const user: User = {
        id: "demo",
        displayName: env.brandName,
        email: `contact@${env.domain.split(":")[0]}`,
    };

    /* SpacePanel : un espace par module. */
    const spaces: Space[] = MODULES.map((m) => ({
        id: m.id,
        label: m.label,
    }));

    /* LeftPanel : items du module actif (placeholder). */
    const sections: NavSection[] = [
        {
            id: "modules",
            title: t("sidebar.spaces"),
            items: MODULES.map((m) => ({
                id: m.id,
                label: m.label,
                active: m.id === activeModule,
                onClick: () => setActiveModule(m.id),
            })),
        },
    ];

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <Sidebar
                spaces={spaces}
                activeSpaceId={activeModule}
                onSpaceClick={(s) => setActiveModule(s.id)}
                sections={sections}
                user={user}
                searchPlaceholder={t("common.search")}
            />
            <main style={{ flex: 1, padding: "48px", background: "var(--ls-color-bg)" }}>
                <h1 style={{ fontSize: "var(--ls-font-size-h2)", color: "var(--ls-color-text)", fontWeight: 600 }}>
                    {t("common.welcome")}
                </h1>
                <p style={{ color: "var(--ls-color-text-secondary)", marginTop: "8px" }}>
                    {t("common.appName")} : {env.brandName}
                </p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px", marginTop: "32px" }}>
                    {MODULES.map((m) => (
                        <a
                            key={m.id}
                            href={m.url}
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "16px",
                                padding: "20px",
                                borderRadius: "var(--ls-radius-md)",
                                border: "1px solid var(--ls-color-border)",
                                textDecoration: "none",
                                color: "var(--ls-color-text)",
                                transition: "border-color 0.1s, background 0.1s",
                            }}
                        >
                            <span style={{
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                width: "44px",
                                height: "44px",
                                borderRadius: "50%",
                                background: "var(--ls-color-primary-subtle)",
                                color: "var(--ls-color-primary-text)",
                                fontSize: "18px",
                                fontWeight: 600,
                            }}>
                                {m.icon}
                            </span>
                            <span style={{ fontWeight: 600, fontSize: "16px" }}>{m.label}</span>
                        </a>
                    ))}
                </div>
            </main>
        </div>
    );
}

/* Boot : init i18n puis render. */
const locale = detectLocale();
initI18n(locale).then(() => {
    createRoot(document.getElementById("root")!).render(<Portal />);
});
