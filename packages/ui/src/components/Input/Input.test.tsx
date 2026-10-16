/*
 * Tests du composant Input.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Input } from "./Input";

describe("Input", () => {
    it("rend un input avec placeholder", () => {
        render(<Input placeholder="Votre nom" />);
        expect(screen.getByPlaceholderText("Votre nom")).toBeInTheDocument();
    });

    it("rend le label au-dessus", () => {
        render(<Input label="Nom complet" />);
        expect(screen.getByText("Nom complet")).toBeInTheDocument();
    });

    it("affiche le message d'erreur", () => {
        render(<Input error="Ce champ est requis" />);
        expect(screen.getByText("Ce champ est requis")).toBeInTheDocument();
    });

    it("marque aria-invalid quand error est present", () => {
        render(<Input error="Erreur" />);
        expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "true");
    });

    it("appelle onChange", () => {
        const handleChange = vi.fn();
        render(<Input onChange={handleChange} />);
        fireEvent.change(screen.getByRole("textbox"), { target: { value: "test" } });
        expect(handleChange).toHaveBeenCalled();
    });
});
