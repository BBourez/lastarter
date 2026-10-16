# Contribuer a LaStarter

## Prerequis

- Node.js >= 22
- pnpm >= 9 (`corepack enable`)
- Docker (pour les tests d'integration)

## Installation

```bash
git clone https://github.com/BBourez/lastarter.git
cd lastarter
pnpm install
```

## Developpement

```bash
# Lancer le serveur de dev (toutes les apps)
pnpm dev

# Tests unitaires
pnpm test

# Tests e2e (necessite un serveur de dev actif)
npx playwright test

# Lint (Biome)
pnpm lint

# Format (Biome)
pnpm format

# Typecheck (TypeScript strict)
cd packages/ui && npx tsc --noEmit
```

## Structure du projet

Voir [ARCHITECTURE.md](./docs/ARCHITECTURE.md) pour la documentation complete.

## Bonnes pratiques

### TDD (Test-Driven Development)

1. Ecrire le test qui echoue (rouge)
2. Ecrire le code minimal qui passe (vert)
3. Refactorer proprement (refactor)

Chaque composant a son fichier de test co-localise :
```
Component/
├── Component.tsx
├── Component.module.css
├── Component.test.tsx
└── index.ts
```

### DDD (Domain-Driven Design)

Les entites metier sont definies dans `packages/api/src/schemas.ts` avec des schemas Zod :
```typescript
export const TransferSchema = z.object({ ... });
export type Transfer = z.infer<typeof TransferSchema>;
```

### TypeScript strict

- Pas de `any` (regle Biome `noExplicitAny`)
- `exactOptionalPropertyTypes` actif
- Tous les fichiers passes par `tsc --noEmit`

### Convention de nommage

- Fichiers composants : `PascalCase.tsx`
- Fichiers hooks : `camelCase.ts`
- Fichiers tests : `*.test.tsx` / `*.test.ts`
- CSS Modules : `*.module.css`
- Types : `PascalCase` (interfaces et type aliases)

### Commits

Format : `type : description courte`

Types : `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

```
feat : ajouter composant Tabs avec navigation clavier
fix : corriger Modal Escape qui ne se propageait pas
docs : ajouter ARCHITECTURE.md avec diagrammes
test : tests pour Zustand store (8 cas)
```

## CI

La CI GitHub Actions verifie :
1. **Lint** : Biome (0 erreur toleree)
2. **Tests** : Vitest (tous doivent passer)
3. **Typecheck** : tsc strict sur les 4 packages

Toutes les etapes sont bloquantes.

## Signaler un bug

Ouvrir une issue avec :
1. Description du probleme
2. Etapes pour reproduire
3. Comportement attendu vs actuel
4. Screenshots si pertinent
