/*
 * LaStarter Portal : point d'entree avec les VRAIS composants Compound.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Les vrais tokens Compound (theme clair + fonts) */
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-base.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-semantic.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-font-fallbacks.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-theme-light-base-mq.css";
/* Les vrais styles des composants Compound */
import "@vector-im/compound-web/dist/style.css";

import React from "react";
import { createRoot } from "react-dom/client";
import { TooltipProvider } from "@vector-im/compound-web";
import { AppShell } from "./AppShell";
import "./portal.css";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Element #root introuvable");

createRoot(rootElement).render(
    <React.StrictMode>
        <TooltipProvider>
            <AppShell />
        </TooltipProvider>
    </React.StrictMode>,
);
