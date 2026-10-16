import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@lastarter/ui": path.resolve(__dirname, "../../packages/ui/src"),
            "@lastarter/i18n": path.resolve(__dirname, "../../packages/i18n/src"),
            "@lastarter/config": path.resolve(__dirname, "../../packages/config/src"),
        },
    },
    build: {
        outDir: "dist",
    },
});
