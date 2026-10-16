# Bonnes pratiques React/TypeScript appliquees dans LaStarter

Ce document resume les bonnes pratiques appliquees, inspirees des tutoriels Grafikart.

## 1. Ne jamais muter l'etat a la racine d'un useEffect

```tsx
// MAL : deux rendus consecutifs
const [loading, setLoading] = useState(true)
useEffect(() => {
    setLoading(true)
    fetchData(url).then(setData).finally(() => setLoading(false))
}, [url])

// BIEN : deriver l'etat de chargement
const [loadedUrl, setLoadedUrl] = useState("")
const loading = loadedUrl !== url
useEffect(() => {
    fetchData(url).then(setData).finally(() => setLoadedUrl(url))
}, [url])
```

Applique dans : tous les hooks TanStack Query (isLoading est derive par la librairie).

## 2. Memoiser les callbacks passes aux composants memoises

```tsx
// MAL : nouvelle fonction a chaque rendu
<MyMemoComponent onClick={() => console.log("clic")} />

// BIEN : callback memoize
const handleClick = useCallback(() => console.log("clic"), [])
<MyMemoComponent onClick={handleClick} />
```

Applique dans : Modal (handleKeyDown memoize avec useCallback).

## 3. Hooks personnalises pour eviter la repetition

```tsx
// useToggle : osciller vrai/faux
const [isOpen, toggle, setOpen] = useToggle(false)

// useClickOutside : fermer un menu au clic exterieur
const ref = useClickOutside<HTMLDivElement>(() => closeMenu())

// useDebouncedValue : debouncer un champ de recherche
const debouncedSearch = useDebouncedValue(searchInput, 300)

// useMediaQuery : responsive
const isMobile = useMediaQuery("(max-width: 768px)")

// useDocumentTitle : titre d'onglet dynamique
useDocumentTitle(`Transferts - ${userName}`)
```

Definis dans : `packages/ui/src/hooks/index.ts`

## 4. createPortal pour les modals

```tsx
// Le Modal est teleporte au body (z-index garanti, pas de problemes d'heritage CSS)
return createPortal(<div className="modal">...</div>, document.body)
```

Applique dans : Modal (rendu via createPortal dans document.body).

## 5. Valeurs derivees plutot qu'etat supplementaire

```tsx
// MAL : stocker une valeur calculee dans l'etat
const [fullname, setFullname] = useState("")
useEffect(() => { setFullname(`${first} ${last}`) }, [first, last])

// BIEN : calculer directement
const fullname = `${first} ${last}`
// Ou avec useMemo si le calcul est couteux
const fullname = useMemo(() => expensiveFormat(first, last), [first, last])
```

Applique dans : Sidebar (sections derivees des props, pas d'etat interne).

## 6. Typage TypeScript strict des composants

```tsx
// Props typees avec interface exportee
export interface ButtonProps {
    kind?: ButtonKind
    size?: ComponentSize
    // ...
}

// forwardRef avec generiques
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(...)

// Contexte avec erreur si pas de provider
export function useAppContext() {
    const value = useContext(AppContext)
    if (value === null) {
        throw new Error("Vous devez entourer ce composant d'un <AppProvider>")
    }
    return value
}
```

## 7. Schemas Zod comme contrats partages (DDD)

```tsx
// Le schema EST le type (approche contrat-first)
export const TransferSchema = z.object({
    id: z.string().uuid(),
    status: TransferStatusSchema,
    // ...
})
export type Transfer = z.infer<typeof TransferSchema>

// Validation runtime des reponses API
const data = TransferSchema.parse(await response.json())
```

Definis dans : `packages/api/src/schemas.ts`

## 8. Nettoyage des effets (cleanup)

```tsx
// Toujours nettoyer les ecouteurs d'evenements
useEffect(() => {
    const handler = () => console.log("scroll")
    window.addEventListener("scroll", handler)
    return () => window.removeEventListener("scroll", handler)
}, [])
```

Applique dans : useClickOutside, useMediaQuery, Modal (Escape listener).
