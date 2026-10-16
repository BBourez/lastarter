/*
 * Tests du composant Avatar.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Avatar } from "./Avatar";

describe("Avatar", () => {
    it("affiche les initiales a partir du nom", () => {
        render(<Avatar name="Jean Dupont" />);
        expect(screen.getByText("JD")).toBeInTheDocument();
    });

    it("affiche maximum 2 initiales", () => {
        render(<Avatar name="Jean Pierre Marie Dupont" />);
        expect(screen.getByText("JP")).toBeInTheDocument();
    });

    it("affiche une image quand src est fourni", () => {
        render(<Avatar name="Jean" src="https://example.com/photo.jpg" />);
        expect(screen.getByRole("img")).toHaveAttribute("src", "https://example.com/photo.jpg");
    });

    it("accepte size=sm", () => {
        render(<Avatar name="J" size="sm" />);
        expect(screen.getByText("J")).toHaveAttribute("data-size", "sm");
    });

    it("accepte size=lg", () => {
        render(<Avatar name="J" size="lg" />);
        expect(screen.getByText("J")).toHaveAttribute("data-size", "lg");
    });
});
