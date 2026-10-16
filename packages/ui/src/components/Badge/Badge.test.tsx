/*
 * Tests du composant Badge.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
    it("rend avec le texte fourni", () => {
        render(<Badge>5</Badge>);
        expect(screen.getByText("5")).toBeInTheDocument();
    });

    it("a data-variant=neutral par defaut", () => {
        render(<Badge>Test</Badge>);
        expect(screen.getByText("Test")).toHaveAttribute("data-variant", "neutral");
    });

    it("accepte variant=danger", () => {
        render(<Badge variant="danger">Alerte</Badge>);
        expect(screen.getByText("Alerte")).toHaveAttribute("data-variant", "danger");
    });
});
