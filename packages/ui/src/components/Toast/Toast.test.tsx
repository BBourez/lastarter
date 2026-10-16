import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Toast } from "./Toast";

describe("Toast", () => {
    it("ne rend rien avec un tableau vide", () => {
        const { container } = render(<Toast toasts={[]} onDismiss={() => {}} />);
        expect(container.firstChild).toBeNull();
    });

    it("rend le message du toast", () => {
        const toasts = [{ id: "1", message: "Fichier envoye" }];
        render(<Toast toasts={toasts} onDismiss={() => {}} />);
        expect(screen.getByText("Fichier envoye")).toBeInTheDocument();
    });

    it("rend plusieurs toasts", () => {
        const toasts = [
            { id: "1", message: "Premier" },
            { id: "2", message: "Second" },
        ];
        render(<Toast toasts={toasts} onDismiss={() => {}} />);
        expect(screen.getByText("Premier")).toBeInTheDocument();
        expect(screen.getByText("Second")).toBeInTheDocument();
    });

    it("appelle onDismiss au clic sur fermer", () => {
        const handleDismiss = vi.fn();
        const toasts = [{ id: "1", message: "Test" }];
        render(<Toast toasts={toasts} onDismiss={handleDismiss} />);
        fireEvent.click(screen.getByLabelText("Fermer"));
        expect(handleDismiss).toHaveBeenCalledWith("1");
    });
});
