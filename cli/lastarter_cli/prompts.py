"""Aides interactives stdlib (input numerote). Le mode --non-interactive ne passe jamais ici."""

from __future__ import annotations

from typing import Sequence


def _clean(text: str) -> str:
    return text.strip().strip(",")


def ask(prompt: str, default: str | None = None) -> str:
    """Question texte libre ; Entrée = valeur par défaut."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        answer = _clean(input(f"{prompt}{suffix} : "))
        if answer:
            return answer
        if default is not None:
            return default
        print("  Une valeur est requise.")


def ask_select(title: str, options: Sequence[str], default_index: int = 0) -> int:
    """Choix unique parmi des options numérotées."""
    print(f"\n{title}")
    for i, option in enumerate(options, start=1):
        marker = "→" if i - 1 == default_index else " "
        print(f"  {marker} {i}) {option}")
    while True:
        raw = input(f"Choix [1-{len(options)}, Entrée={default_index + 1}] : ")
        raw = _clean(raw)
        if not raw:
            return default_index
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("  Choix invalide.")


def ask_checkboxes(
    title: str,
    options: Sequence[str],
    preselected: Sequence[bool],
) -> list[int]:
    """Choix multiple numéroté. Réponse: « 1,3 », « all », « none », Entrée = garder la pré-sélection."""
    print(f"\n{title}")
    for i, (option, checked) in enumerate(zip(options, preselected), start=1):
        marker = "[x]" if checked else "[ ]"
        print(f"  {marker} {i}) {option}")
    hint = ",".join(str(i + 1) for i, c in enumerate(preselected) if c) or "rien"
    while True:
        raw = input(f"Sélection (ex. 1,3 | all | none | Entrée={hint}) : ")
        raw = _clean(raw).lower()
        if not raw:
            return [i for i, c in enumerate(preselected) if c]
        if raw == "all":
            return list(range(len(options)))
        if raw == "none":
            return []
        try:
            indexes = {int(part) - 1 for part in raw.split(",")}
        except ValueError:
            print("  Format invalide (exemples: 1,3 / all / none).")
            continue
        if all(0 <= i < len(options) for i in indexes):
            return sorted(indexes)
        print("  Numéro hors bornes.")
