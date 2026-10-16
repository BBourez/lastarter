/*
 * Tests du composant Modal.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Modal } from "./Modal";

describe("Modal", () => {
    it("ne rend rien quand open=false", () => {
        const { container } = render(
            <Modal open={false} onClose={() => {}}>
                Contenu
            </Modal>,
        );
        expect(container.firstChild).toBeNull();
    });

    it("rend le titre quand open=true", () => {
        render(
            <Modal open={true} onClose={() => {}} title="Mon titre">
                Contenu
            </Modal>,
        );
        expect(screen.getByText("Mon titre")).toBeInTheDocument();
    });

    it("appelle onClose au clic sur l'overlay", () => {
        const handleClose = vi.fn();
        render(
            <Modal open={true} onClose={handleClose}>
                Contenu
            </Modal>,
        );
        fireEvent.click(screen.getByRole("dialog"));
        expect(handleClose).toHaveBeenCalledOnce();
    });

    it("appelle onClose avec la touche Escape", () => {
        const handleClose = vi.fn();
        render(
            <Modal open={true} onClose={handleClose}>
                Contenu
            </Modal>,
        );
        fireEvent.keyDown(document, { key: "Escape" });
        expect(handleClose).toHaveBeenCalledOnce();
    });
});
