# Platform Policies

This directory contains security and governance policies
enforced across ECPS.

Policies may include:
- Pod security and runtime restrictions
- Resource limit enforcement
- Image and registry controls
- Network access rules
- OPA Gatekeeper constraints

All policies are designed to be centrally managed and auditable.

---

## Policy Framework: OPA Gatekeeper

ECPS uses [OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/) to enforce
organization policies automatically.

**Key Points:**
- Policies are defined in Rego (OPA policy language)
- Applied as Kubernetes admission webhooks
- Violations are rejected at deployment time
- No manual policy reviews needed (automated enforcement)

---

## Active Policies

### Security Policies

| Policy | Status | Enforcement |
|--------|--------|-------------|
| **no-privileged-containers** | 🔄 Planned | BLOCK: Containers must not run as root |
| **require-resource-limits** | 🔄 Planned | BLOCK: All containers must have CPU/memory limits |
| **allowed-registries** | 🔄 Planned | BLOCK: Only images from approved registries |
| **pod-security-standards** | 🔄 Planned | WARN: Follow Kubernetes PSS baseline |
| **no-hostnetwork** | 🔄 Planned | BLOCK: Pods cannot use host network namespace |
| **require-securitycontext** | 🔄 Planned | BLOCK: All containers must have securityContext |

### Operational Policies

| Policy | Status | Enforcement |
|--------|--------|-------------|
| **require-labels** | 🔄 Planned | BLOCK: Must have team, app, version labels |
| **require-probes** | 🔄 Planned | WARN: Recommend liveness and readiness probes |
| **max-cpu-limits** | 🔄 Planned | WARN: Limit CPU to 2 cores per pod |
| **image-tag-policy** | 🔄 Planned | BLOCK: No "latest" tags in prod |

### Cost Control Policies

| Policy | Status | Enforcement |
|--------|--------|-------------|
| **resource-efficiency** | 📅 Future | WARN: Requests != limits (over-provisioning) |
| **replica-sanity** | 📅 Future | WARN: Don't run 10 replicas of tiny service |

---

## Quick Start

### View Violations

```bash
# Check current policy violations
kubectl get constraints

# Detailed report
python3 scripts/generate-policy-report.py
```

### Fix a Violation

When deployment is rejected:

```bash
# Error: Container 'app' runs as root (uid=0)

# Fix: Update deployment.yaml
spec:
  containers:
  - name: app
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000

# Retry deployment
kubectl apply -f deployment.yaml
```

### Request Exemption

Rare exceptions can be requested:

```bash
# Email platform-team@company.com with:
# 1. Policy name
# 2. Reason for exemption
# 3. Affected workload
# 4. Duration (temporary or permanent)
```

---

## Policy Examples

### ❌ Blocked: Running as Root

```yaml
# This will be REJECTED
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: app
        image: myimage:latest
        # Missing securityContext → runs as root
```

**Fix**:
```yaml
spec:
  containers:
  - name: app
    image: myimage:latest
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
```

### ❌ Blocked: No Resource Limits

```yaml
# This will be REJECTED
spec:
  containers:
  - name: app
    image: myimage:latest
    # Missing resources section
```

**Fix**:
```yaml
spec:
  containers:
  - name: app
    image: myimage:latest
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
```

### ❌ Blocked: Unauthorized Registry

```yaml
# This will be REJECTED
spec:
  containers:
  - name: app
    image: my-private-registry.io/app:latest  # Not in allowlist
```

**Fix**:
```yaml
spec:
  containers:
  - name: app
    image: docker.io/myapp:v1.2.3  # From approved registry
```

---

## Installation & Deployment

### Prerequisites

- Kubernetes cluster (v1.14+)
- Helm 3.x
- kubectl configured

### Install Gatekeeper

```bash
# Add Helm repo
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm repo update

# Install
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace
```

### Deploy ECPS Policies

```bash
# All policies (once written)
kubectl apply -f policy-templates/
kubectl apply -f policy-constraints/
```

---

## Monitoring

### Policy Violations Dashboard

**Grafana Dashboard**: ECPS Policy Compliance

```
1. Violation Rate (by policy)
2. Compliance % (by namespace)
3. Top Violating Deployments
4. Trend (violations over 30 days)
```

### Alerts

```yaml
# Alert: High policy violation rate
- alert: HighPolicyViolationRate
  expr: rate(gatekeeper_audit_violations_total[5m]) > 10
  annotations:
    summary: "{{ $value }} policy violations in last 5 minutes"
```

### Audit Log

```bash
# View recent policy violations
kubectl logs -n gatekeeper-system -l app=gatekeeper \
  | grep "audit" | tail -20
```

---

## Best Practices

✅ **Do:**
- Keep policies **focused and clear**
- Provide **remediation guides** for every policy
- **Document reasons** for policy decisions
- **Exempt thoughtfully** (with approval process)
- **Monitor compliance** regularly

❌ **Don't:**
- Create **style-based policies** (use linters)
- Make policies so **strict** development becomes painful
- Enforce **without documentation**
- Ignore **false positives**

---

## References

- [OPA Gatekeeper Docs](https://open-policy-agent.github.io/gatekeeper/)
- [Rego Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [CIS Kubernetes Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

---

*Last updated: February 16, 2026*

