/*
 * Diagnostic : rendre ElementShell pour reproduire la page blanche.
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { ElementShell } from "./ElementShell";

describe("Diagnostic ElementShell", () => {
    it("rend sans erreur", () => {
        const { container } = render(
            <ElementShell
                modules={[{ id: "t", label: "Transferts", url: "/t" }]}
                activeModuleId="t"
            >
                <div>Contenu</div>
            </ElementShell>,
        );
        expect(container.firstChild).not.toBeNull();
    });
});
