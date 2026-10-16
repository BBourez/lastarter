/*
 * Tests du composant Button.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "./Button";

describe("Button", () => {
    it("rend avec le texte fourni", () => {
        render(<Button>Cliquer</Button>);
        expect(screen.getByRole("button", { name: "Cliquer" })).toBeInTheDocument();
    });

    it("a data-kind=primary par defaut", () => {
        render(<Button>Test</Button>);
        expect(screen.getByRole("button")).toHaveAttribute("data-kind", "primary");
    });

    it("accepte kind=accent", () => {
        render(<Button kind="accent">Test</Button>);
        expect(screen.getByRole("button")).toHaveAttribute("data-kind", "accent");
    });

    it("accepte size=sm", () => {
        render(<Button size="sm">Test</Button>);
        expect(screen.getByRole("button")).toHaveAttribute("data-size", "sm");
    });

    it("est disabled quand disabled=true", () => {
        render(<Button disabled>Test</Button>);
        expect(screen.getByRole("button")).toBeDisabled();
    });

    it("appelle onClick au clic", () => {
        const handleClick = vi.fn();
        render(<Button onClick={handleClick}>Test</Button>);
        fireEvent.click(screen.getByRole("button"));
        expect(handleClick).toHaveBeenCalledOnce();
    });

    it("rend un lien quand href est fourni", () => {
        render(<Button href="https://example.com">Lien</Button>);
        expect(screen.getByRole("link")).toBeInTheDocument();
    });
});
