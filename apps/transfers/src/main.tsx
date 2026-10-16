/*
 * LaStarter Transfers : application de transfert de fichiers.
 * Frontend neuf avec @lastarter/ui (Sidebar double colonne Element Web).
 * Backend Django existant (API /api/v1.0/).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import {
    Sidebar,
    Button,
    Input,
    Badge,
    type Space,
    type NavSection,
    type User,
} from "@lastarter/ui";
import { initI18n, useTranslation, detectLocale } from "@lastarter/i18n";
import { createQueryClient, formatFileSize } from "@lastarter/api";
import { requireAuth } from "@lastarter/config";
import { useSentTransfers, useReceivedTransfers, useCurrentUser, useCreateTransfer } from "./hooks/useTransfers";

/* ==================== PAGE : NOUVEAU TRANSFERT ==================== */

function NewTransferPage() {
    const { t } = useTranslation();
    const createTransfer = useCreateTransfer();
    const [emails, setEmails] = useState("");
    const [message, setMessage] = useState("");
    const [duration, setDuration] = useState("7");
    const [files, setFiles] = useState<File[]>([]);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (files.length === 0) return;
        const emailList = emails.split(",").map((s) => s.trim()).filter(Boolean);
        if (emailList.length === 0) return;
        try {
            await createTransfer.mutateAsync({
                emails: emailList,
                files,
                message: message || undefined,
                duration: `${duration}_days`,
            });
            setSuccess(true);
            setEmails("");
            setMessage("");
            setFiles([]);
        } catch {
            /* Erreur geree par le hook */
        }
    };

    if (success) {
        return (
            <div style={{ maxWidth: 480, margin: "0 auto", padding: "48px 24px", textAlign: "center" }}>
                <h2>Transfert envoye</h2>
                <p style={{ color: "var(--ls-color-text-secondary)", marginTop: 8 }}>
                    Vos destinataires recevront un email avec le lien de telechargement.
                </p>
                <Button kind="primary" onClick={() => setSuccess(false)} style={{ marginTop: 24 }}>
                    Nouveau transfert
                </Button>
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit} style={{ maxWidth: 480, margin: "0 auto", padding: "48px 24px", display: "flex", flexDirection: "column", gap: 20 }}>
            <h2>{t("nav.transfersNew")}</h2>

            <Input
                label="Envoyer a (emails separes par des virgules)"
                type="text"
                value={emails}
                onChange={(e) => setEmails(e.target.value)}
                placeholder="jean@acme.com, marie@acme.com"
                required
            />

            <Input
                label="Duree de validite (jours)"
                type="number"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                min={1}
                max={30}
            />

            <Input
                label="Message (optionnel)"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Message pour vos destinataires"
            />

            <div>
                <label style={{ display: "block", fontSize: 13, fontWeight: 500, marginBottom: 6, color: "var(--ls-color-text)" }}>
                    Fichiers
                </label>
                <input
                    type="file"
                    multiple
                    onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                    style={{ fontSize: 14, color: "var(--ls-color-text-secondary)" }}
                />
                {files.length > 0 && (
                    <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 4 }}>
                        {files.map((f) => (
                            <span key={f.name} style={{ fontSize: 13, color: "var(--ls-color-text-secondary)" }}>
                                {f.name} ({formatFileSize(f.size)})
                            </span>
                        ))}
                    </div>
                )}
            </div>

            <Button type="submit" kind="accent" disabled={createTransfer.isPending || files.length === 0}>
                {createTransfer.isPending ? "Envoi en cours..." : "Envoyer"}
            </Button>
        </form>
    );
}

/* ==================== PAGE : LISTE TRANSFERTS ==================== */

function TransferListPage({ mode }: { mode: "sent" | "received" }) {
    const query = mode === "sent" ? useSentTransfers() : useReceivedTransfers();

    if (query.isLoading) return <div style={{ padding: 48 }}>Chargement...</div>;
    if (query.error) return <div style={{ padding: 48 }}>Erreur de chargement</div>;

    const transfers = query.data ?? [];

    return (
        <div style={{ padding: "48px 24px" }}>
            <h2>{mode === "sent" ? "Transferts envoyes" : "Transferts recus"}</h2>
            {transfers.length === 0 ? (
                <p style={{ color: "var(--ls-color-text-secondary)", marginTop: 16 }}>Aucun transfert</p>
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
                    {transfers.map((t) => (
                        <div key={t.id} style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 12,
                            padding: "12px 16px",
                            borderRadius: "var(--ls-radius-md)",
                            border: "1px solid var(--ls-color-border)",
                        }}>
                            <Badge variant={t.status === "sent" ? "success" : "warning"}>{t.status}</Badge>
                            <span style={{ flex: 1, fontWeight: 500 }}>{t.subject || "Sans objet"}</span>
                            <span style={{ fontSize: 13, color: "var(--ls-color-text-secondary)" }}>
                                {t.files?.length ?? 0} fichiers
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

/* ==================== APP PRINCIPALE ==================== */

type Page = "new" | "sent" | "received" | "settings";

function TransfersApp() {
    const { t } = useTranslation();
    const [page, setPage] = useState<Page>("new");
    const userQuery = useCurrentUser();

    const user: User = {
        id: "me",
        displayName: userQuery.data?.full_name ?? "...",
        email: userQuery.data?.email ?? "",
    };

    const spaces: Space[] = [
        { id: "transfers", label: t("nav.transfers") },
    ];

    const sections: NavSection[] = [
        {
            id: "main",
            items: [
                { id: "new", label: t("nav.transfersNew"), active: page === "new", onClick: () => setPage("new") },
                { id: "sent", label: t("nav.transfersSent"), active: page === "sent", onClick: () => setPage("sent") },
                { id: "received", label: t("nav.transfersReceived"), active: page === "received", onClick: () => setPage("received") },
            ],
        },
    ];

    return (
        <div style={{ display: "flex", height: "100vh" }}>
            <Sidebar
                spaces={spaces}
                activeSpaceId="transfers"
                sections={sections}
                user={user}
                searchPlaceholder={t("common.search")}
                onSettingsClick={() => setPage("settings")}
            />
            <main style={{ flex: 1, overflowY: "auto", background: "var(--ls-color-bg)" }}>
                {page === "new" && <NewTransferPage />}
                {page === "sent" && <TransferListPage mode="sent" />}
                {page === "received" && <TransferListPage mode="received" />}
                {page === "settings" && <div style={{ padding: 48 }}>Parametres (a venir)</div>}
            </main>
        </div>
    );
}

/* ==================== BOOT ==================== */

const queryClient = createQueryClient();
const locale = detectLocale();

requireAuth("transfers");

initI18n(locale).then(() => {
    createRoot(document.getElementById("root")!).render(
        <QueryClientProvider client={queryClient}>
            <TransfersApp />
        </QueryClientProvider>,
    );
});
