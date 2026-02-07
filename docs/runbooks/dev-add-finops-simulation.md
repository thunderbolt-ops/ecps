# Runbook: Add FinOps Simulation to ECPS Dev

## Purpose

Provide a simple, internal-only FinOps view for ECPS dev by:

- Deriving "virtual cost" metrics from requested CPU and memory
- Aggregating cost per namespace (and per team)
- Visualizing cost in Grafana

This is a simulation only, using arbitrary "credits" instead of real currency.

---

## Preconditions

- Dev cluster is running: context `kind-ecps-dev`
- kube-prometheus-stack is installed in `platform-observability` (per bootstrap runbook)
- Terraform for dev (`infra/envs/dev`) is working

---

## Step 1 — Ensure dev context

Run from: anywhere

```bash
kubectl config use-context kind-ecps-dev
kubectl config current-context
