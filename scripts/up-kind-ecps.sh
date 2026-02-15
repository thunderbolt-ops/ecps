#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/up-kind-ecps.sh [dev|stage]
ENV=${1:-dev}
CLUSTER_NAME=ecps-stage
KIND_CONF=kind-ecps-stage.yaml

echo "Starting local ECPS bring-up (env=$ENV)"

# Check docker access
if [ ! -S /var/run/docker.sock ]; then
  echo "Docker socket not found at /var/run/docker.sock" >&2
  exit 1
fi
if ! docker ps >/dev/null 2>&1; then
  echo "Cannot access Docker daemon. Ensure your user can access Docker (add to docker group or run newgrp docker)." >&2
  exit 1
fi

# Create kind cluster if missing
if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
  echo "Kind cluster ${CLUSTER_NAME} already exists"
else
  echo "Creating kind cluster ${CLUSTER_NAME} using ${KIND_CONF}"
  kind create cluster --name "${CLUSTER_NAME}" --config "${KIND_CONF}"
fi

# Ensure kubeconfig/context exists for the cluster and use it
KUBECTX="kind-${CLUSTER_NAME}"
if ! kubectl config get-contexts -o name | grep -q "^${KUBECTX}$"; then
  echo "kubectl context ${KUBECTX} not found — exporting kubeconfig from kind"
  kind export kubeconfig --name "${CLUSTER_NAME}"
fi
kubectl config use-context "${KUBECTX}"

# Install ingress-nginx for kind
echo "Installing ingress-nginx"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl -n ingress-nginx wait --for=condition=available deployment --all --timeout=2m

# Terraform apply infra for env
TF_DIR="infra/envs/${ENV}"
if [ -d "$TF_DIR" ]; then
  echo "Initializing Terraform in $TF_DIR"
  pushd "$TF_DIR" >/dev/null
  # Ensure Prometheus operator CRDs are present before Terraform applies PrometheusRule manifests
  if ! kubectl get crd prometheusrules.monitoring.coreos.com >/dev/null 2>&1; then
    if ! command -v helm >/dev/null 2>&1; then
      echo "helm not found; please install helm to deploy Prometheus operator" >&2
      exit 1
    fi
    echo "Installing kube-prometheus-stack CRDs and chart (Prometheus operator) via Helm"
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
    helm repo update || true
    TMPDIR=$(mktemp -d)
    echo "Pulling chart to ${TMPDIR} to extract CRDs"
    helm pull prometheus-community/kube-prometheus-stack --untar --untardir "$TMPDIR" || true
    if [ -d "$TMPDIR/kube-prometheus-stack/crds" ]; then
      echo "Applying CRDs from chart"
      kubectl apply -f "$TMPDIR/kube-prometheus-stack/crds"
    else
      echo "CRDs folder not found in pulled chart; continuing to helm install which may install CRDs"
    fi
    echo "Installing helm chart (will wait for readiness)"
    helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace --wait --timeout 5m || true
    rm -rf "$TMPDIR"
    echo "Waiting for PrometheusRule CRD to be available..."
    for i in {1..60}; do
      if kubectl get crd prometheusrules.monitoring.coreos.com >/dev/null 2>&1; then
        echo "PrometheusRule CRD available"
        break
      fi
      sleep 2
    done
  else
    echo "PrometheusRule CRD already present"
  fi

  terraform init -backend=false
  terraform apply -auto-approve
  popd >/dev/null
else
  echo "Terraform env dir $TF_DIR not found, skipping Terraform" >&2
fi

# Build and load images used by manifests
# We build the apps under apps/team-alpha/* that have Dockerfiles
APPS_DIRS=(
  "apps/team-alpha/billing-api"
  "apps/team-alpha/jobs-api"
  "apps/team-alpha/jobs-worker"
  "apps/team-alpha/reporting-api"
)

for app in "${APPS_DIRS[@]}"; do
  if [ -f "$app/Dockerfile" ]; then
    image_name=$(basename "$app")
    # Map to manifest expected names
    case "$image_name" in
      billing-api) tag="ecps-billing-api:0.1.0" ;;
      jobs-api)    tag="ecps-jobs-api:0.1.0" ;;
      jobs-worker) tag="ecps-jobs-worker:0.1.0" ;;
      reporting-api) tag="ecps-reporting-api:0.1.0" ;;
      *) tag="${image_name}:local" ;;
    esac
    echo "Building $app -> $tag"
    docker build -t "$tag" "$app"
    echo "Loading $tag into kind"
    kind load docker-image "$tag" --name "$CLUSTER_NAME"
  else
    echo "No Dockerfile in $app, skipping"
  fi
done

# Apply Kubernetes manifests for apps (team-alpha)
echo "Applying Kubernetes manifests"
kubectl apply -R -f apps/team-alpha || true

# Wait for pods
echo "Waiting for pods to be ready (2m)"
kubectl wait --for=condition=Ready pods --all --timeout=120s -A || true

echo "Pods status:"
kubectl get pods -A

echo "Services and ingress:"
kubectl get svc -A
kubectl get ing -A || true

echo "Done. If apps are not healthy, check pod logs with 'kubectl logs -n <ns> <pod>'"
