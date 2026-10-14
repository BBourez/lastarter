"""Chargement et validation du catalogue de briques (catalogue/*.toml)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SECRET_PATTERN = "{secret:"


@dataclass(frozen=True)
class Brick:
    """Une brique du catalogue — définition canonique du format (cf. catalogue/SCHEMA.md)."""

    name: str
    title: str
    category: str
    description: str
    license: str
    upstream_repo: str
    upstream_pin: str
    core: bool = False
    requires: list[str] = field(default_factory=list)
    maturity: str = "stable"  # stable | planned
    extra_secrets: list[str] = field(default_factory=list)  # ex. realm as-code
    oidc: dict = field(default_factory=dict)
    branding_env: dict = field(default_factory=dict)
    branding_custom_theme: dict = field(default_factory=dict)
    env: dict = field(default_factory=dict)
    compose: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    @property
    def is_selectable(self) -> bool:
        return self.maturity == "stable"


def _load_brick(path: Path) -> tuple[Brick | None, str | None]:
    """Charge un manifeste ; retourne (brick, erreur)."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        return None, f"{path.name}: TOML invalide ({exc})"

    brick_data = data.get("brick")
    if not isinstance(brick_data, dict):
        return None, f"{path.name}: section [brick] manquante"

    required_keys = ("name", "title", "category", "license", "upstream_repo", "upstream_pin")
    missing = [k for k in required_keys if not brick_data.get(k)]
    if missing:
        return None, f"{path.name}: [brick] clés manquantes: {', '.join(missing)}"

    maturity = brick_data.get("maturity", "stable")
    if maturity not in ("stable", "planned"):
        return None, f"{path.name}: maturity invalide {maturity!r} (stable|planned)"

    brick = Brick(
        name=str(brick_data["name"]),
        title=str(brick_data["title"]),
        category=str(brick_data["category"]),
        description=str(brick_data.get("description", "")),
        license=str(brick_data["license"]),
        upstream_repo=str(brick_data["upstream_repo"]),
        upstream_pin=str(brick_data["upstream_pin"]),
        core=bool(brick_data.get("core", False)),
        requires=[str(r) for r in brick_data.get("requires", [])],
        maturity=maturity,
        extra_secrets=[str(s) for s in brick_data.get("extra_secrets", [])],
        oidc=dict(data.get("oidc", {})),
        branding_env=dict(data.get("branding", {}).get("env", {})),
        branding_custom_theme=dict(data.get("branding", {}).get("custom_theme", {})),
        env=dict(data.get("env", {})),
        compose=dict(data.get("compose", {})),
        notes=dict(data.get("notes", {})),
    )
    return brick, None


def load_catalogue(catalogue_dir: Path) -> tuple[dict[str, Brick], list[str]]:
    """Charge tous les manifestes ; retourne (bricks, erreurs de cohérence)."""
    bricks: dict[str, Brick] = {}
    errors: list[str] = []
    for path in sorted(catalogue_dir.glob("*.toml")):
        brick, error = _load_brick(path)
        if error:
            errors.append(error)
            continue
        if brick.name in bricks:
            errors.append(f"{path.name}: brique {brick.name!r} déjà définie")
            continue
        bricks[brick.name] = brick

    # Cohérence des dépendances et absence de cycle.
    for brick in bricks.values():
        for dep in brick.requires:
            if dep not in bricks:
                errors.append(f"{brick.name}: dépendance inconnue {dep!r}")
    for brick in bricks.values():
        seen: set[str] = set()
        stack = [brick.name]
        while stack:
            current = stack.pop()
            if current == brick.name and seen:
                errors.append(f"{brick.name}: cycle de dépendances")
                break
            if current in seen:
                continue
            seen.add(current)
            stack.extend(bricks[current].requires if current in bricks else [])
    return bricks, errors


def resolve_selection(selected: list[str], bricks: dict[str, Brick]) -> tuple[list[str], list[str]]:
    """Complète la sélection avec les dépendances (et les briques core).

    Retourne (ordre_dinstallation, briques_ajoutees_automatiquement).
    L'ordre garantit qu'une brique vient après ses dépendances.
    """
    unknown = [name for name in selected if name not in bricks]
    if unknown:
        raise KeyError(f"briques inconnues: {', '.join(unknown)}")

    needed: set[str] = set()
    for name in selected:
        needed.add(name)
        stack = list(bricks[name].requires)
        while stack:
            dep = stack.pop()
            if dep in needed:
                continue
            needed.add(dep)
            stack.extend(bricks[dep].requires)

    for brick in bricks.values():
        if brick.core:
            needed.add(brick.name)

    # Tri : dépendances d'abord (tri topologique par passes).
    ordered: list[str] = []
    remaining = dict.fromkeys(needed, None)
    while remaining:
        ready = [n for n in remaining if all(d in ordered for d in bricks[n].requires)]
        if not ready:  # cycle déjà signalé par load_catalogue ; garde-fou.
            ordered.extend(remaining)
            break
        for name in sorted(ready):
            ordered.append(name)
            del remaining[name]

    added = [name for name in ordered if name not in selected]
    return ordered, added


def find_catalogue(start: Path) -> Path | None:
    """Cherche le dossier catalogue/ en remontant depuis `start`, puis près du package."""
    for candidate in [start, *start.resolve().parents]:
        probe = candidate / "catalogue"
        if probe.is_dir() and any(probe.glob("*.toml")):
            return probe
    package_relative = Path(__file__).resolve().parents[2] / "catalogue"
    if package_relative.is_dir():
        return package_relative
    return None


def iter_secret_specs(brick: Brick) -> list[tuple[str, str]]:
    """Spécifications de secrets d'une brique : (nom, format).

    Sources : env (`{secret:NAME}`), extra_secrets (syntaxe « name » ou « name:b64 »
    — b64 = base64 standard de 32 octets, ex. clé ed25519 de signature Matrix).
    """
    specs: dict[str, str] = {}
    for entry in brick.extra_secrets:
        name, _, fmt = entry.partition(":")
        specs[name] = fmt or "urlsafe"
    for value in brick.env.values():
        value = str(value)
        if SECRET_PATTERN in value:
            after = value.split(SECRET_PATTERN, 1)[1]
            name = after.split("}", 1)[0]
            if name:
                specs.setdefault(name, "urlsafe")
    return sorted(specs.items())


def secret_names(brick: Brick) -> list[str]:
    """Noms des secrets référencés par une brique (env `{secret:NAME}` + extra_secrets)."""
    return [name for name, _fmt in iter_secret_specs(brick)]
