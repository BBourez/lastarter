/*
 * LaStarter Transfers : avec ElementShell (vrais composants Compound).
 * Backend Django existant (API /api/v1.0/).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/* Les vrais tokens + styles Compound */
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-base.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-common-semantic.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-font-fallbacks.css";
import "@vector-im/compound-design-tokens/assets/web/css/cpd-theme-light-base-mq.css";
import "@vector-im/compound-web/dist/style.css";

import { createQueryClient, formatFileSize } from "@lastarter/api";
import { ElementShell, type ShellModule } from "@lastarter/ui";
import { QueryClientProvider } from "@tanstack/react-query";
import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import {
    Body,
    Button,
    Heading,
    TextButton,
} from "@vector-im/compound-web";
import {
    useCreateTransfer,
    useReceivedTransfers,
    useSentTransfers,
} from "./hooks/useTransfers";
import "./transfers.css";

/* Modules du LeftPanel pour cette app */
const MODULES: ShellModule[] = [
    { id: "transfers", label: "Transferts", url: "http://transfers.localhost/" },
    { id: "projects", label: "Projets", url: "http://projects.localhost/" },
    { id: "chat", label: "Discussions", url: "http://chat.localhost/", badge: 3 },
    { id: "meet", label: "Reunions", url: "http://meet.localhost/" },
];

/* ==================== PAGE : NOUVEAU TRANSFERT ==================== */

function NewTransferPage() {
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
            <div className="tr_Page">
                <Heading size="md" weight="medium">Transfert envoye</Heading>
                <Body size="md" className="tr_Muted">
                    Vos destinataires recevront un email avec le lien de telechargement.
                </Body>
                <Button kind="primary" onClick={() => setSuccess(false)}>Nouveau transfert</Button>
            </div>
        );
    }

    return (
        <form onSubmit={handleSubmit} className="tr_Page tr_Form">
            <Heading size="md" weight="medium">Nouveau transfert</Heading>

            <label className="tr_Label">
                Envoyer a (emails separes par des virgules)
                <input
                    className="tr_Input"
                    type="text"
                    value={emails}
                    onChange={(e) => setEmails(e.target.value)}
                    placeholder="jean@acme.com, marie@acme.com"
                    required
                />
            </label>

            <label className="tr_Label">
                Duree de validite (jours)
                <input
                    className="tr_Input"
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    min={1}
                    max={30}
                />
            </label>

            <label className="tr_Label">
                Message (optionnel)
                <input
                    className="tr_Input"
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Message pour vos destinataires"
                />
            </label>

            <label className="tr_Label">
                Fichiers
                <input
                    className="tr_FileInput"
                    type="file"
                    multiple
                    onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                />
                {files.length > 0 && (
                    <div className="tr_FileList">
                        {files.map((f) => (
                            <span key={f.name}>{f.name} ({formatFileSize(f.size)})</span>
                        ))}
                    </div>
                )}
            </label>

            <Button
                type="submit"
                kind="primary"
                disabled={createTransfer.isPending || files.length === 0}
            >
                {createTransfer.isPending ? "Envoi en cours..." : "Envoyer"}
            </Button>
        </form>
    );
}

/* ==================== PAGE : LISTE TRANSFERTS ==================== */

function TransferListPage({ mode }: { mode: "sent" | "received" }) {
    const query = mode === "sent" ? useSentTransfers() : useReceivedTransfers();

    if (query.isLoading) return <div className="tr_Page">Chargement...</div>;
    if (query.error) return <div className="tr_Page">Erreur de chargement</div>;

    const transfers = query.data ?? [];

    return (
        <div className="tr_Page">
            <Heading size="md" weight="medium">
                {mode === "sent" ? "Transferts envoyes" : "Transferts recus"}
            </Heading>
            {transfers.length === 0 ? (
                <Body size="md" className="tr_Muted">Aucun transfert.</Body>
            ) : (
                <div className="tr_List">
                    {transfers.map((tr) => (
                        <div key={tr.id} className="tr_ListItem">
                            <span className="tr_ListLabel">{tr.message || "Transfert"}</span>
                            <span className="tr_Muted">{tr.files.length} fichier(s)</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

/* ==================== APP ==================== */

function TransfersApp() {
    const [page, setPage] = useState<"new" | "sent" | "received">("new");

    return (
        <ElementShell modules={MODULES} activeModuleId="transfers">
            <header className="ls_PageHeader">
                <Body as="h1" size="lg" weight="medium">Transferts</Body>
                <TextButton onClick={() => setPage(page === "new" ? "sent" : "new")}>
                    {page === "new" ? "Voir les envoyes" : "Nouveau transfert"}
                </TextButton>
            </header>
            <div className="ls_PageBody">
                {page === "new" && <NewTransferPage />}
                {page === "sent" && <TransferListPage mode="sent" />}
                {page === "received" && <TransferListPage mode="received" />}
            </div>
        </ElementShell>
    );
}

/* ==================== BOOTSTRAP ==================== */

const queryClient = createQueryClient();
const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Element #root introuvable");

createRoot(rootElement).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <TransfersApp />
        </QueryClientProvider>
    </React.StrictMode>,
);
