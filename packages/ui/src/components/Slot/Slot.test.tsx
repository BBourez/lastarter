/*
 * Tests du composant Slot (pattern asChild).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Slot } from "./Slot";

describe("Slot", () => {
    it("transfere les className a l'enfant", () => {
        render(
            <Slot className="parent-class">
                <a href="/test" className="child-class">Lien</a>
            </Slot>,
        );
        const link = screen.getByRole("link");
        expect(link.className).toContain("parent-class");
        expect(link.className).toContain("child-class");
    });

    it("transfere les props a l'enfant", () => {
        render(
            <Slot data-testid="custom-id">
                <button type="button">Clique</button>
            </Slot>,
        );
        expect(screen.getByTestId("custom-id")).toBeInTheDocument();
    });

    it("le style de l'enfant gagne sur le parent", () => {
        render(
            <Slot style={{ color: "red", fontSize: "14px" }}>
                <button type="button" style={{ color: "blue" }}>Test</button>
            </Slot>,
        );
        const button = screen.getByRole("button");
        expect(button.style.color).toBe("blue");
        expect(button.style.fontSize).toBe("14px");
    });

    it("leve une erreur avec plusieurs enfants", () => {
        expect(() =>
            render(
                <Slot>
                    <span>Premier</span>
                    <span>Second</span>
                </Slot>,
            ),
        ).toThrow("Slot must have exactly one child element");
    });
});
