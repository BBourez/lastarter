import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Typography } from "./Typography";

describe("Typography", () => {
    it("rend un h1 par defaut pour variant h1", () => {
        render(<Typography variant="h1">Titre principal</Typography>);
        const h1 = screen.getByRole("heading", { level: 1 });
        expect(h1).toBeInTheDocument();
        expect(h1).toHaveTextContent("Titre principal");
    });

    it("rend un p pour variant body", () => {
        render(<Typography variant="body">Texte du corps</Typography>);
        expect(screen.getByText("Texte du corps")).toBeInTheDocument();
    });

    it("accepte color secondary", () => {
        render(
            <Typography variant="body" color="secondary">
                Texte gris
            </Typography>,
        );
        expect(screen.getByText("Texte gris")).toBeInTheDocument();
    });

    it("rend avec un tag personnalise", () => {
        render(
            <Typography variant="body" as="div">
                Dans une div
            </Typography>,
        );
        expect(screen.getByText("Dans une div").tagName).toBe("DIV");
    });
});
