import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@lastarter/ui": path.resolve(__dirname, "../../packages/ui/src"),
        },
    },
    server: {
        proxy: {
            // En dev : proxy l'API vers le backend Docker
            "/api": {
                target: "https://transfers.localhost:8443",
                changeOrigin: true,
                secure: false,
            },
        },
    },
    build: {
        outDir: "dist",
        assetsDir: "assets",
    },
});
