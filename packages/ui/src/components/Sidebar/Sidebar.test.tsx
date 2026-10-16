/*
 * Tests du composant Sidebar.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar } from "./Sidebar";

const mockUser = {
    id: "u1",
    displayName: "Jean Dupont",
    email: "jean@acme.com",
};

const mockSpaces = [
    { id: "sp1", label: "Transferts" },
    { id: "sp2", label: "Projets" },
];

const mockSections = [
    {
        id: "sec1",
        title: "Navigation",
        items: [
            { id: "item1", label: "Mes fichiers", active: true },
            { id: "item2", label: "Favoris" },
        ],
    },
];

describe("Sidebar", () => {
    it("rend le nom de l'utilisateur", () => {
        render(
            <Sidebar
                spaces={mockSpaces}
                sections={mockSections}
                user={mockUser}
            />,
        );
        expect(screen.getByText("Jean Dupont")).toBeInTheDocument();
    });

    it("rend l'email de l'utilisateur", () => {
        render(
            <Sidebar
                spaces={mockSpaces}
                sections={mockSections}
                user={mockUser}
            />,
        );
        expect(screen.getByText("jean@acme.com")).toBeInTheDocument();
    });

    it("rend tous les espaces", () => {
        render(
            <Sidebar
                spaces={mockSpaces}
                sections={mockSections}
                user={mockUser}
            />,
        );
        expect(screen.getByTitle("Transferts")).toBeInTheDocument();
        expect(screen.getByTitle("Projets")).toBeInTheDocument();
    });

    it("marque l'espace actif", () => {
        render(
            <Sidebar
                spaces={mockSpaces}
                activeSpaceId="sp1"
                sections={mockSections}
                user={mockUser}
            />,
        );
        expect(screen.getByTitle("Transferts")).toHaveAttribute("data-active", "true");
    });

    it("appelle onSpaceClick au clic", () => {
        const handleSpaceClick = vi.fn();
        render(
            <Sidebar
                spaces={mockSpaces}
                onSpaceClick={handleSpaceClick}
                sections={mockSections}
                user={mockUser}
            />,
        );
        fireEvent.click(screen.getByTitle("Projets"));
        expect(handleSpaceClick).toHaveBeenCalledWith(mockSpaces[1]);
    });

    it("rend les items de navigation", () => {
        render(
            <Sidebar
                spaces={mockSpaces}
                sections={mockSections}
                user={mockUser}
            />,
        );
        expect(screen.getByText("Mes fichiers")).toBeInTheDocument();
        expect(screen.getByText("Favoris")).toBeInTheDocument();
    });

    it("rend le bouton parametres", () => {
        const handleSettings = vi.fn();
        render(
            <Sidebar
                spaces={mockSpaces}
                sections={mockSections}
                user={mockUser}
                onSettingsClick={handleSettings}
            />,
        );
        const settingsButton = screen.getByLabelText("Parametres");
        expect(settingsButton).toBeInTheDocument();
        fireEvent.click(settingsButton);
        expect(handleSettings).toHaveBeenCalledOnce();
    });

    it("rend la barre de recherche", () => {
        const handleSearch = vi.fn();
        render(
            <Sidebar
                spaces={mockSpaces}
                sections={mockSections}
                user={mockUser}
                onSearchClick={handleSearch}
            />,
        );
        fireEvent.click(screen.getByRole("button", { name: /rechercher/i }));
        expect(handleSearch).toHaveBeenCalledOnce();
    });
});
