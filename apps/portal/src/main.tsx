/*
 * LaStarter Portal : avec ElementShell partage (vrais composants Compound).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Les vrais tokens + styles Compound (importes par ElementShell via @lastarter/ui,
   mais on les importe aussi ici pour garantir l'ordre de chargement CSS). */
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-base.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-semantic.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-font-fallbacks.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-theme-light-base-mq.css";
import "@vector-im/compound-web/dist/style.css";

import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { Body, TextButton, TooltipProvider } from "@vector-im/compound-web";
import { ElementShell, type ShellModule } from "@lastarter/ui";

/* Modules du LeftPanel pour le portal */
const MODULES: ShellModule[] = [
    { id: "transfers", label: "Transferts", url: "http://transfers.localhost/", badge: 2 },
    { id: "projects", label: "Projets", url: "http://projects.localhost/" },
    { id: "chat", label: "Discussions", url: "http://chat.localhost/", badge: 3 },
    { id: "meet", label: "Reunions", url: "http://meet.localhost/" },
];

function Portal() {
    const [activeModule, setActiveModule] = useState("transfers");
    const mod = MODULES.find((m) => m.id === activeModule) ?? MODULES[0];

    return (
        <ElementShell modules={MODULES} activeModuleId={activeModule}>
            <header className="ls_PageHeader">
                <Body as="h1" size="lg" weight="medium">{mod.label}</Body>
                <TextButton>Nouveau</TextButton>
            </header>
            <div className="ls_PageBody">
                <Body size="md" style={{ color: "var(--cpd-color-text-secondary)" }}>
                    Module {mod.label} : ouvrez {mod.url}
                </Body>
            </div>
        </ElementShell>
    );
}

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Element #root introuvable");

createRoot(rootElement).render(
    <React.StrictMode>
        <TooltipProvider>
            <Portal />
        </TooltipProvider>
    </React.StrictMode>,
);
