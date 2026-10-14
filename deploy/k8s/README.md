# deploy/k8s/ — cible Kubernetes (phase 5)

Helm umbrella consommant les charts amont quand ils existent (meet en publie un
officiel — cf. `.github/workflows/release-helm-chart.yaml` amont) et des charts
communautaires éprouvés sinon (synapse, keycloak…).

Même contrat que compose : les briques du manifeste client déterminent les
sous-charts activés ; secrets injectés via external-secrets/SOPS (phase 6).
