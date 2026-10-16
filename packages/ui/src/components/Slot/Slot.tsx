/*
 * LaStarter UI : Slot pour le pattern asChild (cf. Grafikart "asChild").
 * Transfere les props du parent a l'enfant unique (pattern Radix UI).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import {
    Children,
    cloneElement,
    isValidElement,
    type HTMLAttributes,
    type PropsWithChildren,
    type ReactElement,
    type ReactNode,
} from "react";

/** Type utilitaire pour les composants supportant asChild. */
export type AsChildProps<BaseProps, SecondaryProps> =
    | ({ asChild: true; children: ReactNode } & BaseProps & {
            [K in keyof SecondaryProps]: never;
        })
    | ({ asChild?: false } & BaseProps & SecondaryProps);

/** Fusionner deux classes CSS (sans twMerge pour rester zero-dep). */
function mergeClasses(...classes: (string | undefined)[]): string | undefined {
    const valid = classes.filter(Boolean);
    return valid.length > 0 ? valid.join(" ") : undefined;
}

/** Fusionner deux styles (le style de l'enfant gagne). */
function mergeStyles(
    parent: React.CSSProperties | undefined,
    child: React.CSSProperties | undefined,
): React.CSSProperties | undefined {
    if (!parent && !child) return undefined;
    return { ...parent, ...child };
}

/**
 * Slot : transfere les props recues a l'enfant unique.
 * Utilise avec `asChild` pour rendre des composants polymorphiques.
 *
 * @example
 * <Button asChild>
 *   <a href="/lien">Voir le site</a>
 * </Button>
 */
export function Slot(props: PropsWithChildren<HTMLAttributes<HTMLElement>>) {
    const children = Children.toArray(props.children).filter(isValidElement);

    if (children.length !== 1) {
        throw new Error("Slot must have exactly one child element");
    }

    const child = children[0] as ReactElement<HTMLAttributes<HTMLElement>>;

    return cloneElement(child, {
        ...props,
        ...child.props,
        style: mergeStyles(props.style, child.props.style),
        className: mergeClasses(props.className, child.props.className),
    });
}
