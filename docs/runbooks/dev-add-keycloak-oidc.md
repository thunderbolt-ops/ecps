# Runbook: Add Keycloak OIDC to ECPS Dev

## Purpose

Add a basic Keycloak identity provider to ECPS dev with:

- Namespace: `platform-identity`
- Ingress host: `keycloak.platform.local`
- Admin user: `admin`
- Admin password: `ChangeMeNow123!` (dev only, configured via Terraform)

---

## Precondition

- Dev cluster exists: `kind-ecps-dev`
- Ingress NGINX is installed and port-forwarded on `8080 -> 80`
- Argo CD and observability already working (per dev bootstrap runbook)

---

## Step 1 — Ensure dev kube context

Run from: anywhere

```bash
kubectl config use-context kind-ecps-dev
kubectl config current-context
