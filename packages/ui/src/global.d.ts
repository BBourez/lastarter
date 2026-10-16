/* Declarations pour les CSS modules (imports *.module.css). */

declare module "*.module.css" {
    const classes: Record<string, string>;
    export default classes;
}

declare module "*.css" {
    const classes: Record<string, string>;
    export default classes;
}
