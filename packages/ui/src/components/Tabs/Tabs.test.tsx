import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Tabs } from "./Tabs";

const items = [
    { id: "tab1", label: "Onglet 1" },
    { id: "tab2", label: "Onglet 2" },
    { id: "tab3", label: "Onglet 3" },
];

describe("Tabs", () => {
    it("rend tous les onglets", () => {
        render(<Tabs items={items} activeId="tab1" onChange={() => {}} />);
        expect(screen.getByRole("tab", { name: "Onglet 1" })).toBeInTheDocument();
        expect(screen.getByRole("tab", { name: "Onglet 2" })).toBeInTheDocument();
        expect(screen.getByRole("tab", { name: "Onglet 3" })).toBeInTheDocument();
    });

    it("marque l'onglet actif", () => {
        render(<Tabs items={items} activeId="tab2" onChange={() => {}} />);
        expect(screen.getByRole("tab", { name: "Onglet 2" })).toHaveAttribute(
            "aria-selected",
            "true",
        );
        expect(screen.getByRole("tab", { name: "Onglet 1" })).toHaveAttribute(
            "aria-selected",
            "false",
        );
    });

    it("appelle onChange au clic", () => {
        const handleChange = vi.fn();
        render(<Tabs items={items} activeId="tab1" onChange={handleChange} />);
        fireEvent.click(screen.getByRole("tab", { name: "Onglet 2" }));
        expect(handleChange).toHaveBeenCalledWith("tab2");
    });

    it("ne repond pas au clic sur un onglet disabled", () => {
        const handleChange = vi.fn();
        const disabledItems = [{ id: "d1", label: "Disabled", disabled: true }];
        render(<Tabs items={disabledItems} activeId="d1" onChange={handleChange} />);
        fireEvent.click(screen.getByRole("tab"));
        expect(handleChange).not.toHaveBeenCalled();
    });
});
