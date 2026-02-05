# Observability Architecture (Development Environment)

ECPS uses a centralized observability stack per Kubernetes cluster.

## Components

- Prometheus Operator
- Prometheus (metrics collection and storage)
- Alertmanager (alert routing – configured later)
- Grafana (dashboards and visualization)

## Scope

- Cluster-level metrics (nodes, pods, namespaces)
- Platform component metrics (Ingress, Argo CD later)
- Application metrics (added incrementally)

## Principles

- Observability is platform-owned
- Application teams expose metrics; they do not run Prometheus
- Dashboards and alerts are version-controlled

This stack is first deployed in `ecps-dev` and will be replicated
with stricter settings in stage and prod.
