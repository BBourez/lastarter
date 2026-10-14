# lastarter/scripts/reset-demo.sh
# Reset complet d'un environnement démo (toutes les 3 mois par ex).
# Détruit tout, régénère des credentials neufs, redéploie.
#
# Usage : ./reset-demo.sh demo demo.lastarter.app
#
# Prérequis DNS : un wildcard *.demo.lastarter.app → IP du serveur
# Prérequis TLS : certificat wildcard *.demo.lastarter.app (Let's Encrypt DNS-01)

set -euo pipefail

CLIENT="${1:?Usage: reset-demo.sh <client> <domain> [bricks]}"
DOMAIN="${2:?Usage: reset-demo.sh <client> <domain> [bricks]}"
BRICKS="${3:-drive,element-web,messages,element-call,transfers}"
CLI_DIR="$(dirname "$0")/../cli"

echo "=== RESET COMPLET : $CLIENT ($DOMAIN) ==="
echo "Briques : $BRICKS"
echo ""

# 1. Arrêter et supprimer les conteneurs
echo "--- 1/5 Arrêt des conteneurs ---"
cd "$CLI_DIR"
python -m lastarter_cli deploy --client "$CLIENT" --down 2>/dev/null || true

# 2. Supprimer les volumes (données + DB)
echo "--- 2/5 Suppression des volumes (données effacées) ---"
VOLUMES=$(docker volume ls -q --filter "label=com.docker.compose.project=$CLIENT")
if [ -n "$VOLUMES" ]; then
    docker volume rm $VOLUMES
    echo "  Supprimés : $VOLUMES"
else
    echo "  Aucun volume"
fi

# 3. Supprimer l'arbre de déploiement (secrets + config)
echo "--- 3/5 Suppression de la configuration et des secrets ---"
rm -rf "../deployments/$CLIENT"
echo "  Supprimé : deployments/$CLIENT/"

# 4. Régénérer (credentials neufs automatiquement)
echo "--- 4/5 Régénération avec credentials neufs ---"
python -m lastarter_cli init \
    --non-interactive \
    --client "$CLIENT" \
    --domain "$DOMAIN" \
    --bricks "$BRICKS"

# 5. Redéployer
echo "--- 5/5 Redéploiement ---"
python -m lastarter_cli deploy --client "$CLIENT" --pull

echo ""
echo "=== RESET TERMINÉ ==="
echo "  Nouveaux credentials dans : deployments/$CLIENT/secrets.env"
echo "  URLs :"
grep "https://" "../deployments/$CLIENT/README.md" | head -10 || true
