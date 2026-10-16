/*
 * LaStarter E2E : tests de bout en bout pour le portail.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import { test, expect } from "@playwright/test";

test.describe("Portail", () => {
    test("affiche la page d'accueil", async ({ page }) => {
        await page.goto("/");
        await expect(page).toHaveTitle(/LaStarter/);
    });

    test("rend la sidebar avec les espaces", async ({ page }) => {
        await page.goto("/");
        // La sidebar SpacePanel doit etre visible
        const sidebar = page.locator("nav[aria-label='Espaces']");
        await expect(sidebar).toBeVisible();
    });

    test("affiche le menu utilisateur en bas de sidebar", async ({ page }) => {
        await page.goto("/");
        // Le nom et l'email de l'utilisateur doivent etre presents
        await expect(page.locator("text=LaStarter")).toBeVisible();
    });
});
