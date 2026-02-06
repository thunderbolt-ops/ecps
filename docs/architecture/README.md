# ECPS Architecture Overview

## 1. Purpose

ECPS (Enterprise Cloud Platform Simulator) is a **local, production-inspired
Platform Engineering lab** designed to demonstrate how a modern Internal
Developer Platform (IDP) is structured, operated, and governed.

The platform runs entirely on a single Ubuntu host using `kind`, but follows
patterns used in real multi-tenant Kubernetes platforms:
- GitOps as the source of truth
- Namespace-based tenancy
- Network isolation
- Observability and SRE practices
- Explicit RBAC and identity boundaries

This repository is intentionally structured to reflect how a real platform
team would separate concerns across infrastructure, platform services,
applications, SRE, and documentation.

---

## 2. High-Level Architecture

At a high level, ECPS consists of:

- A local Kubernetes cluster (`kind`)
- Platform services installed and managed by Terraform + Helm
- GitOps (Argo CD) driving all application and platform state
- Namespace-isolated application teams
- Shared ingress and observability layers
- Explicit SLOs, alerts, and incident runbooks

All components are deployed declaratively and reconciled continuously.

---

## 3. Component Overview

### 3.1 Kubernetes Cluster

- Kubernetes distribution: `kind`
- Purpose:
  - Simulate a real Kubernetes control plane
  - Allow repeatable creation and teardown
- Scope:
  - Single control-plane node
  - One or more worker nodes
- Non-goals:
  - High availability
  - Cloud-provider integrations

---

### 3.2 GitOps (Argo CD)

- Argo CD is the **control plane for desired state**
- All workloads (platform + apps) are defined in Git
- Manual `kubectl` changes are treated as drift and reconciled

Responsibilities:
- Sync Kubernetes manifests from GitHub
- Detect and correct drift
- Provide visibility into application health

---

### 3.3 Application Teams

Each team is represented by:
- A dedicated namespace (`team-alpha`, `team-beta`)
- A Git folder under `apps/<team>/`
- Independent ingress routes
- Isolated NetworkPolicies
- Namespace-scoped RBAC

This enables:
- Clear blast-radius boundaries
- Independent deployments
- Team autonomy without cluster-wide access

---

### 3.4 Ingress Layer

- Ingress controller: NGINX
- Deployed centrally in `platform-system`
- Routes traffic based on hostnames:
  - `hello.team-alpha.local`
  - `hello.team-beta.local`

Design goals:
- Shared infrastructure, isolated routing
- No per-team ingress controllers
- Simple, auditable ingress rules

---

### 3.5 Observability

Observability is treated as a **platform responsibility**, not a per-team concern.

Components:
- Prometheus (metrics collection & alert evaluation)
- kube-state-metrics
- Grafana (dashboards)
- Alertmanager (alert routing – stubbed for lab)

Key principles:
- Platform-level SLOs and alerts
- Alerts defined close to Prometheus (PrometheusRule CRDs)
- Dashboards are informational, not the source of truth

---

### 3.6 Security & Identity

Security is enforced using:
- Namespace boundaries
- NetworkPolicies (default-deny + explicit allows)
- Kubernetes RBAC mapped to logical identity groups

Identity model:
- `team-alpha-developers` → access only to `team-alpha`
- `team-beta-developers` → access only to `team-beta`
- `platform-engineers` → cluster-wide admin access

No shared credentials or implicit permissions.

---

## 4. Failure & Recovery Model

ECPS explicitly models failure scenarios:

- Application outage (replicas = 0)
- Ingress returning 503
- Alerts firing after defined thresholds
- Recovery via GitOps

Incidents are:
- Detected via Prometheus
- Diagnosed using runbooks
- Resolved by restoring Git state
- Documented post-incident

This mirrors real SRE workflows.

---

## 5. Non-Goals

ECPS deliberately does NOT attempt to:
- Be production-ready
- Replace managed Kubernetes
- Model cloud-specific primitives (LBs, IAM, etc.)

The goal is **clarity of platform design**, not infrastructure realism.

---

## 6. Audience

This architecture is intended for:
- Platform engineers
- SREs
- Cloud architects
- Technical interview discussions

It is optimized for **explainability and signal**, not scale.
