# SLO: Hello App Availability (team-alpha & team-beta)

## 1. Overview

This SLO defines the target availability for the `hello-app` services running in the `team-alpha` and `team-beta` namespaces on the ECPS platform.

These apps are simple HTTP services exposed via the shared ingress controller under:

- `hello.team-alpha.local`
- `hello.team-beta.local`

While the services are demo workloads, they represent the “golden path” for validating that the platform, ingress, and team isolation are all working correctly.

---

## 2. Services in Scope

- Kubernetes namespaces:
  - `team-alpha`
  - `team-beta`
- Deployments:
  - `hello-app` (one per namespace)
- Ingress:
  - `team-alpha/hello-app` with host `hello.team-alpha.local`
  - `team-beta/hello-app` with host `hello.team-beta.local`

---

## 3. SLI Definition

### 3.1 Conceptual SLI (user perspective)

**SLI (conceptual)** = percentage of successful HTTP 2xx/3xx responses for:

- `GET http://hello.team-alpha.local/`
- `GET http://hello.team-beta.local/`

over a rolling time window (e.g., 30 days).

Formally:

\[
SLI = \frac{\text{count of successful HTTP requests}}{\text{total HTTP requests}} \times 100
\]

In a real environment this would typically be measured using:
- Ingress controller/request metrics (NGINX, Envoy, ALB, etc.)
- Or an external synthetic probe (blackbox exporter, synthetic tests, etc.)

### 3.2 Lab Implementation SLI (cluster perspective)

For the local ECPS lab, we approximate availability by checking whether **all `hello-app` pods are Ready**.

Per namespace:

- `kube_pod_container_status_ready{namespace="<team>", pod=~"hello-app-.*"}`

We define a binary SLI per namespace:

- SLI = 1 when **at least one Ready container** exists in the `hello-app` deployment.
- SLI = 0 when **no Ready containers** exist (service effectively unavailable).

Approximate per-namespace SLI query (Prometheus):

```promql
sum by (namespace) (
  max_over_time(
    kube_pod_container_status_ready{namespace=~"team-alpha|team-beta", pod=~"hello-app-.*"}[5m]
  )
)
