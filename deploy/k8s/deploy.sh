#!/usr/bin/env bash
# LaStarter kind — déploiement de la tranche Keycloak (realm as-code) + Drive
# (chart amont pinné) à travers l'ingress. Idempotent (ré-exécutable).
#
# Prérequis : cluster kind-lastarter prêt (deploy/k8s/kind/kind-config.yaml),
# helm + kubectl dans $HOME/.lastarter-bin, chart drive en lecture seule à
# ../examples/drive/src/helm/drive (relatif au dépôt, surchargeable par
# CHART_DRIVE).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
K8S_DIR="$REPO_ROOT/deploy/k8s"
RUNTIME="$K8S_DIR/.runtime"
CHART_DRIVE="${CHART_DRIVE:-$REPO_ROOT/../examples/drive/src/helm/drive}"
NS=lastarter

export PATH="$HOME/.lastarter-bin:$PATH"

command -v kubectl >/dev/null || { echo "ERREUR : kubectl requis" >&2; exit 1; }
command -v helm >/dev/null || { echo "ERREUR : helm requis ($HOME/.lastarter-bin)" >&2; exit 1; }
[ -d "$CHART_DRIVE" ] || { echo "ERREUR : chart drive introuvable : $CHART_DRIVE" >&2; exit 1; }

current="$(kubectl config current-context)"
if [ "$current" != "kind-lastarter" ]; then
  echo "ERREUR : contexte kubectl inattendu '$current' (attendu kind-lastarter)" >&2
  exit 1
fi

echo "== 1/5 Rendu realm + secrets (deploy/k8s/.runtime, idempotent)"
python "$K8S_DIR/kind/render-realm.py"

echo "== 2/5 Secrets k8s (rendus, gitignorés)"
kubectl apply -f "$K8S_DIR/manifests/00-namespace.yaml"
kubectl apply -f "$RUNTIME/secret-postgres.yaml" \
              -f "$RUNTIME/secret-keycloak.yaml" \
              -f "$RUNTIME/secret-drive.yaml" \
              -f "$RUNTIME/secret-keycloak-theme.yaml"
kubectl -n "$NS" create secret generic keycloak-realm \
  --from-file=lastarter-realm.json="$RUNTIME/realm-lastarter.json" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "== 3/5 Infra + keycloak + ingress (manifests)"
kubectl apply -f "$K8S_DIR/manifests"

echo "== 4/5 Attente ready"
kubectl -n "$NS" rollout status deploy/postgres --timeout=240s
kubectl -n "$NS" rollout status deploy/valkey --timeout=120s
kubectl -n "$NS" rollout status deploy/rustfs --timeout=120s
kubectl -n "$NS" rollout status deploy/keycloak --timeout=300s
kubectl -n "$NS" wait --for=condition=complete job/s3-init --timeout=180s

echo "== 5/5 Brique Drive (chart amont : $CHART_DRIVE)"
helm upgrade --install drive "$CHART_DRIVE" -n "$NS" \
  -f "$K8S_DIR/values-drive.yaml" -f "$RUNTIME/values-drive-secrets.yaml"
kubectl -n "$NS" rollout status deploy/drive-backend --timeout=420s
kubectl -n "$NS" rollout status deploy/drive-frontend --timeout=180s

echo
echo "Déploiement terminé. Fumée (ports hôtes kind : 8080 -> ingress HTTP) :"
echo "  curl -s -o /dev/null -w '%{http_code}\\n' http://id.localhost:8080/realms/lastarter/.well-known/openid-configuration"
echo "  curl -s -o /dev/null -w '%{http_code}\\n' http://drive.localhost:8080/"
echo "Connexion démo : demo / $(grep '^demo_user_password=' "$RUNTIME/secrets.env" | cut -d= -f2)"
echo "Console admin Keycloak : admin / $(grep '^kc_admin_password=' "$RUNTIME/secrets.env" | cut -d= -f2)"
echo "Superuser drive /admin : admin@lastarter.local / $(grep '^drive_superuser_password=' "$RUNTIME/secrets.env" | cut -d= -f2)"
