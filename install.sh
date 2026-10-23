#!/usr/bin/env bash
#
# LaStarter — installateur « une ligne » : dépôt + CLI + (option) déploiement.
#
#   curl -fsSL https://raw.githubusercontent.com/BBourez/lastarter/main/install.sh | bash
#
# Variables (toutes optionnelles) :
#   LASTARTER_HOME      dossier cible (défaut : ~/.lastarter)
#   LASTARTER_CLIENT    nom du client          → bascule en mode non interactif
#   LASTARTER_DOMAIN    domaine principal (ex. acme.example.com)
#   LASTARTER_APPS      briques (ex. drive,discussions,meet ; vide = core seul)
#   LASTARTER_THEME     palette (ex. element-light / element-dark)
#   LASTARTER_LOGO      fichier logo (.svg/.png) à copier
#   LASTARTER_OUTPUT    racine des déploiements (défaut : <home>/deployments)
#   LASTARTER_DEPLOY=1  déploie (docker compose) juste après init
#
# Idempotent : ré-exécuter = mise à jour du dépôt + rejeu init (pré-rempli,
# logo conservé) + redéploiement si LASTARTER_DEPLOY=1.

set -euo pipefail

REPO_URL="https://github.com/BBourez/lastarter"
LASTARTER_HOME="${LASTARTER_HOME:-$HOME/.lastarter}"

log() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mattention :\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merreur :\033[0m %s\n' "$*" >&2; exit 1; }

# --- 1. Prérequis -----------------------------------------------------------

command -v bash >/dev/null 2>&1 || die "bash est requis."

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then PY="$(command -v python || true)"; fi
if [ -z "$PY" ]; then
  die "Python >= 3.12 requis : aucun 'python3'/'python' trouvé dans le PATH."
fi
"$PY" - <<'PYCHECK' >/dev/null 2>&1 || die "Python >= 3.12 requis. La CLI est stdlib-only : aucune dépendance à installer."
import sys
sys.exit(0 if sys.version_info >= (3, 12) else 1)
PYCHECK

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    log "Docker + plugin compose : OK ($(docker --version))"
  else
    warn "Docker présent sans le plugin compose (installer 'docker-compose-plugin') — 'deploy' échouera."
  fi
else
  warn "Docker absent (https://docs.docker.com/engine/install/) — le dépôt et la CLI s'installent, mais 'deploy' échouera."
fi

# --- 2. Dépôt (git clone --depth 1, ou tarball codeload si git absent) ------

fetch_with_git() {
  if [ -f "$LASTARTER_HOME/.git/config" ]; then
    git -C "$LASTARTER_HOME" fetch --depth 1 origin main
    git -C "$LASTARTER_HOME" reset --hard FETCH_HEAD
  else
    rm -rf "$LASTARTER_HOME"
    git clone --depth 1 "$REPO_URL" "$LASTARTER_HOME"
  fi
}

fetch_with_tarball() {
  command -v curl >/dev/null 2>&1 || command -v wget >/dev/null 2>&1 \
    || die "ni git ni curl/wget : impossible de récupérer le dépôt."
  local tmp
  tmp="$(mktemp -d)"
  log "git absent — téléchargement du tarball (branche main)"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "https://codeload.github.com/BBourez/lastarter/tar.gz/refs/heads/main" -o "$tmp/lastarter.tar.gz"
  else
    wget -qO "$tmp/lastarter.tar.gz" "https://codeload.github.com/BBourez/lastarter/tar.gz/refs/heads/main"
  fi
  rm -rf "$LASTARTER_HOME"
  mkdir -p "$LASTARTER_HOME"
  tar -xzf "$tmp/lastarter.tar.gz" -C "$LASTARTER_HOME" --strip-components=1
  rm -rf "$tmp"
}

if command -v git >/dev/null 2>&1; then
  fetch_with_git
else
  fetch_with_tarball
fi
log "Dépôt à jour : $LASTARTER_HOME"

# --- 3. Wrapper CLI (bin/lastarter) -----------------------------------------

mkdir -p "$LASTARTER_HOME/bin"
cat > "$LASTARTER_HOME/bin/lastarter" <<WRAPPER
#!/usr/bin/env bash
# Wrapper lastarter-cli — généré par install.sh ; zéro dépendance (stdlib).
set -euo pipefail
LASTARTER_DIR="\${LASTARTER_HOME:-$HOME/.lastarter}"
cd "\$LASTARTER_DIR"
export PYTHONPATH="\$LASTARTER_DIR/cli\${PYTHONPATH:+:\$PYTHONPATH}"
if command -v python3 >/dev/null 2>&1; then
  exec python3 -m lastarter_cli "\$@"
fi
exec python -m lastarter_cli "\$@"
WRAPPER
chmod +x "$LASTARTER_HOME/bin/lastarter"

# --- 4. Vérification ---------------------------------------------------------

"$LASTARTER_HOME/bin/lastarter" list >/dev/null 2>&1 \
  || die "la CLI ne démarre pas (interpréteur : $PY) — relancer avec bash -x pour diagnostiquer."
log "CLI opérationnelle : $LASTARTER_HOME/bin/lastarter"

case ":$PATH:" in
  *":$LASTARTER_HOME/bin:"*) : ;;
  *)
    log "Pour utiliser 'lastarter' partout :"
    printf '    export PATH="%s:$PATH"\n' "$LASTARTER_HOME/bin"
    ;;
esac

# --- 5. Mode scripté (init + déploiement optionnel) --------------------------

INTERACTIVE=1
if [ "${LASTARTER_NONINTERACTIVE:-}" = "1" ]; then INTERACTIVE=0; fi
if [ -n "${LASTARTER_CLIENT:-}" ] && [ -n "${LASTARTER_DOMAIN:-}" ]; then INTERACTIVE=0; fi

if [ "$INTERACTIVE" -eq 1 ]; then
  log "Installation terminée. Lancez : $LASTARTER_HOME/bin/lastarter init"
  exit 0
fi

: "${LASTARTER_CLIENT:?LASTARTER_CLIENT requis en mode non interactif}"
: "${LASTARTER_DOMAIN:?LASTARTER_DOMAIN requis en mode non interactif}"

# Slug identique à slugify() de la CLI (dossier deployments/<slug>).
SLUG="$("$PY" - "$LASTARTER_CLIENT" <<'PYS'
import re, sys, unicodedata
normalized = unicodedata.normalize("NFKD", sys.argv[1]).encode("ascii", "ignore").decode()
print(re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "client")
PYS
)"

INIT_ARGS=(init --non-interactive --client "$LASTARTER_CLIENT" --domain "$LASTARTER_DOMAIN" --bricks "${LASTARTER_APPS:-}")
if [ -n "${LASTARTER_THEME:-}" ]; then INIT_ARGS+=(--theme "$LASTARTER_THEME"); fi
if [ -n "${LASTARTER_LOGO:-}" ]; then INIT_ARGS+=(--logo "$LASTARTER_LOGO"); fi
if [ -n "${LASTARTER_OUTPUT:-}" ]; then INIT_ARGS+=(--output "$LASTARTER_OUTPUT"); fi

log "Configuration du déploiement « $LASTARTER_CLIENT » ($LASTARTER_DOMAIN)"
(cd "$LASTARTER_HOME" && ./bin/lastarter "${INIT_ARGS[@]}")

if [ "${LASTARTER_DEPLOY:-}" = "1" ]; then
  command -v docker >/dev/null 2>&1 || die "LASTARTER_DEPLOY=1 mais docker est absent."
  log "Déploiement (docker compose — premier lancement : quelques minutes)"
  (cd "$LASTARTER_HOME" && ./bin/lastarter deploy --client "$SLUG" --pull)
  (cd "$LASTARTER_HOME" && ./bin/lastarter ps --client "$SLUG") || true
else
  log "Prêt. Pour déployer : cd \"$LASTARTER_HOME\" && ./bin/lastarter deploy --client \"$SLUG\" --pull"
fi
log "Terminé."
