/* Declarations d'environnement pour @lastarter/config (Vite + Node). */

interface ImportMetaEnv {
    readonly [key: string]: string | undefined;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}

declare const process: {
    env: Record<string, string | undefined>;
};
