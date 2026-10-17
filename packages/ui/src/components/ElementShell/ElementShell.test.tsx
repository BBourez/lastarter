import { render } from "@testing-library/react";
/*
 * Diagnostic : rendre ElementShell pour reproduire la page blanche.
 */
import { describe, expect, it } from "vitest";
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
