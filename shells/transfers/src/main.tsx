/*
 * LaStarter Shell — Transfers.
 * Wrapper Element Web : sidebar avec user menu + iframe de l'app originale.
 * L'app originale tourne dans une iframe (même origine via proxy nginx)
 * — sa sidebar/header sont masqués par le CSS du shell.
 */

import React, { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { LaStarterShell, type SidebarUser } from "@lastarter/ui";

/* ================================================================
 * Récupération de l'utilisateur depuis l'API Transfers
 * ================================================================ */

interface CurrentUser {
    email: string;
    full_name: string;
}

async function fetchUser(): Promise<SidebarUser> {
    try {
        const resp = await fetch("/api/v1.0/users/me/", { credentials: "include" });
        if (!resp.ok) throw new Error("not authenticated");
        const data: CurrentUser = await resp.json();
        return {
            displayName: data.full_name || data.email.split("@")[0],
            email: data.email,
        };
    } catch {
        // Pas connecté : l'auto-login.js redirigera vers Keycloak
        return { displayName: "…", email: "…" };
    }
}

/* ================================================================
 * Navigation Transfers
 * ================================================================ */

const navSections = [
    {
        title: "Transferts",
        items: [
            { icon: "📨", label: "Nouveau transfert", href: "#new", active: true },
            { icon: "📤", label: "Envoyés", href: "#sent" },
            { icon: "📥", label: "Reçus", href: "#received" },
        ],
    },
];

/* ================================================================
 * App
 * ================================================================ */

function App() {
    const [user, setUser] = useState<SidebarUser>({ displayName: "Chargement…", email: "" });

    useEffect(() => {
        fetchUser().then(setUser);
    }, []);

    return (
        <LaStarterShell
            appName="Transfers"
            navSections={navSections}
            user={user}
            onSettings={() => {
                document.getElementById("app-frame")?.contentWindow?.location.assign("/app/settings/");
            }}
            onUserProfile={() => {
                // Ouvrir le dropdown profil de l'app
            }}
            searchPlaceholder="Rechercher un transfert…"
        >
            <div className="shell-frame-container">
                <iframe
                    id="app-frame"
                    src="/app/"
                    title="Transfers"
                    className="shell-frame"
                    sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
                />
            </div>
        </LaStarterShell>
    );
}

createRoot(document.getElementById("lastarter-root")!).render(<App />);
