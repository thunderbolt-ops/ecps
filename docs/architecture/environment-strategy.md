# Environment Strategy

**How ECPS uses distinct environments (dev, stage, prod) and manages promotion between them.**

This document covers:
- Environment design principles
- Configuration differences
- Promotion workflows
- Disaster recovery considerations

---

## 🏗️ Environment Overview

ECPS implements **three distinct Kubernetes clusters** to simulate realistic multi-environment architecture:

```
┌─────────────────────────────────────────────────────────┐
│  Dev Cluster (kind-ecps-dev)                           │
│  - Fast iteration, loose policies                      │
│  - Lower resource requests, 1x replicas               │
│  - For developers and feature testing                 │
└─────────────────────────────────────────────────────────┘
                        ↓ Promote
┌─────────────────────────────────────────────────────────┐
│  Stage Cluster (kind-ecps-stage)                       │
│  - Production-like, strict policies                    │
│  - Medium resource requests, 2x replicas              │
│  - For integration testing and validation             │
└─────────────────────────────────────────────────────────┘
                        ↓ Promote
┌─────────────────────────────────────────────────────────┐
│  Prod Cluster (kind-ecps-prod) [Skeleton]             │
│  - Max strictness, all guards enabled                  │
│  - High resource requests, 3x+ replicas              │
│  - For live customer workloads                        │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 Dev Environment (Development)

### Purpose
**Enable fast iteration and debugging without heavy constraints**

- Developers rapidly deploy changes
- Minimal operational overhead
- Failures are expected and tolerated
- Cost is secondary to velocity

### Configuration

| Aspect | Dev | Justification |
|--------|-----|---------------|
| **Cluster** | Single node | Minimal resource usage |
| **Replicas** | 1x | Fast restart cycles |
| **Resource Requests** | Low (100m CPU, 128Mi RAM) | Save resources |
| **Timeouts** | Relaxed (120s) | Avoid flaky tests |
| **Liveness Probes** | Disabled or lenient | Faster debugging |
| **Policy Enforcement** | Loose | Don't block experimentation |
| **SLO Monitoring** | Basic | Not production-critical |
| **Backup/Recovery** | None | Data is ephemeral |
| **Cost** | ~$30-50/month | Low-priority resource |
| **Data Retention** | 7 days | Save disk space |

### Example Deployment (Dev)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: billing-api
  namespace: team-alpha
spec:
  replicas: 1  # Single replica for speed
  template:
    spec:
      containers:
      - name: billing-api
        image: ecps-billing-api:dev-latest  # Weekly builds OK
        resources:
          requests:
            cpu: 100m
            memory: 128Mi  # Minimal
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          disabled: true  # Faster feedback loops
        env:
        - name: LOG_LEVEL
          value: "DEBUG"  # Verbose logging for debugging
        - name: DB_TIMEOUT
          value: "120"  # Generous timeout
```

### Developer Workflow

```bash
# 1. Make code change
edit src/main.py

# 2. Quick test locally
python -m pytest tests/

# 3. Build and deploy to dev (immediate)
docker build -t ecps-billing-api:dev-latest .
kind load docker-image ecps-billing-api:dev-latest --name ecps-dev
kubectl rollout restart deployment/billing-api -n team-alpha

# 4. Verify in dev
kubectl port-forward svc/billing-api 8080:80 -n team-alpha
curl http://localhost:8080/health

# 5. When ready, commit and push
git add .
git commit -m "feat: add invoice export endpoint"
git push origin feature/invoice-export
```

### Who Has Access?

- ✅ **Team developers**: Full access to team-alpha namespace
- ✅ **Platform engineers**: Full cluster access
- ❌ **Customers**: No access

---

## 🔄 Stage Environment (Staging)

### Purpose
**Validate changes are production-ready before customer exposure**

- Production configuration and policies applied
- Integration testing with realistic data
- Performance and reliability validation
- SLO compliance verification
- Smoke testing before prod deployment

### Configuration

| Aspect | Stage | Justification |
|--------|-------|---------------|
| **Cluster** | Multi-node | Production-like topology |
| **Replicas** | 2x | Test failover scenarios |
| **Resource Requests** | Medium (200m CPU, 256Mi RAM) | Production-like |
| **Timeouts** | Standard (60s) | Match prod behavior |
| **Liveness Probes** | Enabled | Production-like recovery |
| **Policy Enforcement** | Strict | Catch policy violations |
| **SLO Monitoring** | Full | Track SLO attainment |
| **Backup/Recovery** | Nightly backup | Validate backup process |
| **Cost** | ~$75/month | Similar to prod |
| **Data Retention** | 30 days | Business data archive |

### Example Deployment (Stage)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: billing-api
  namespace: team-alpha
spec:
  replicas: 2  # Account for pod disruptions
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0  # Ensure availability during upgrades
  template:
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - billing-api
              topologyKey: kubernetes.io/hostname
      containers:
      - name: billing-api
        image: ecps-billing-api:v1.2.3  # Semantic versioning
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: DB_TIMEOUT
          value: "60"
        - name: ENVIRONMENT
          value: "staging"
```

### Promotion Criteria (from Dev → Stage)

Before promoting to stage, a release must:

- ✅ **Code review**: Approved by 2 engineers
- ✅ **Tests passing**: 100% unit test pass rate
- ✅ **Lint checks**: No significant issues
- ✅ **Build success**: Docker image builds cleanly
- ✅ **Dependency audit**: No critical CVEs introduced
- ✅ **Documentation**: Changes documented (API changes, config, etc.)
- ✅ **Changelog**: Entry added to CHANGELOG
- ✅ **Version bump**: Semantic version incremented

**Gate Check:**
```bash
# Automated checklist
bin/promote-to-stage.sh

OUTPUT:
✅ Code review approved (2 approvals)
✅ CI/CD pipeline passed
✅ Image scan: 0 critical CVEs
✅ Unit tests: 42/42 passing
✅ Lint: 0 errors
✅ CHANGELOG updated
✅ Version bumped (v1.2.2 → v1.2.3)

Ready to promote? (y/n) y
→ Creating stage release...
→ Deploying to stage cluster
→ Running smoke tests...
All checks passed! Release deployed to stage.
```

### Stage Validation Procedure

```bash
# 1. Monitor stage environment
kubectl logs -f deployment/billing-api -n team-alpha

# 2. Run integration test suite
pytest tests/integration/ -v --live-endpoint=https://stage-api.internal

# 3. Run SLO validation
- Verify 99.5% availability SLO is met
- Confirm latency p95 < 500ms
- Check error rate < 0.1%

# 4. Run load test (if resource-heavy feature)
locust -f tests/load/locustfile.py \
  --host=https://stage-api.internal \
  --users=100 --spawn-rate=10

# 5. Manual smoke test
curl https://stage-api.internal/health
curl -X POST https://stage-api.internal/api/v1/invoices \
  -H "Content-Type: application/json" \
  -d '{"team": "team-alpha", "total": 100}'

# 6. Approve for production
echo "✅ Stage validation passed"
```

### Rollback Procedure (if issues found in Stage)

```bash
# If problems discovered:
1. Immediately rollback using GitOps
   git revert HEAD~1
   git push origin main
   
2. ArgoCD automatically syncs to previous version
   kubectl rollout status deployment/billing-api -n team-alpha

3. Document issue in incident tracker
4. Root cause analysis before next promotion attempt
```

---

## 🚀 Prod Environment (Production)

### Purpose
**Serve real customer workloads with maximum reliability**

- Every deployment is validated and careful
- All safety guards enabled
- SLOs are not aspirational—they're critical
- Incident response is immediate
- Cost is justified by business value

### Configuration

| Aspect | Prod | Justification |
|--------|------|---------------|
| **Cluster** | Multi-node HA | Zero single points of failure |
| **Replicas** | 3x+ | Handle node failures gracefully |
| **Resource Requests** | High (500m CPU, 512Mi RAM) | Prevent resource contention |
| **Timeouts** | Conservative (30s) | Fast failure detection |
| **Liveness Probes** | Aggressive | Rapid recovery from failures |
| **Policy Enforcement** | Max | Prevent misconfigurations |
| **SLO Monitoring** | Real-time | Immediate alert on breach |
| **Backup/Recovery** | Hourly + PITR | Comprehensive disaster recovery |
| **Cost** | ~$150-200/month | Performance justified by value |
| **Data Retention** | 90+ days | Regulatory/audit compliance |
| **Canary Deployments** | Enabled | 5% traffic before full rollout |

### Example Deployment (Prod)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: billing-api
  namespace: team-alpha
  labels:
    team: team-alpha
    env: prod
    criticality: high
spec:
  replicas: 3  # 99.5% availability requires redundancy
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0    # Never drop below 3 replicas
      maxSurge: 1          # Smooth rolling updates
  template:
    metadata:
      labels:
        app: billing-api
        version: v1.2.3
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:  # MUST spread
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - billing-api
            topologyKey: kubernetes.io/hostname
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsReadOnlyRootFilesystem: true
      containers:
      - name: billing-api
        image: ecps-billing-api:v1.2.3  # Exact semver
        imagePullPolicy: IfNotPresent
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2  # Restart after 2 failures (10s)
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 2
          failureThreshold: 3
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "WARN"
        - name: METRICS_ENABLED
          value: "true"
        - name: TRACE_SAMPLING
          value: "1.0"  # 100% tracing in prod
      podDisruptionBudget:
        minAvailable: 2  # 3 replicas - 2 = at most 1 pod disruption
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: billing-api-pdb
  namespace: team-alpha
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: billing-api
```

### Promotion Criteria (from Stage → Prod)

Before promoting to prod, a release must:

- ✅ **Staged validation**: Passed all stage tests
- ✅ **SLO verification**: Staging SLOs met for 24+ hours
- ✅ **Load test**: Verified under expected peak load
- ✅ **Security scan**: No vulnerabilities found
- ✅ **Runbook update**: Incident procedures documented
- ✅ **Change log**: Clear entry for production
- ✅ **Approvals**: Approval from on-call lead AND engineering manager
- ✅ **Canary plan**: Defined canary deployment strategy

**Promotion Checklist:**
```
PRODUCTION RELEASE CHECKLIST – billing-api v1.2.3

Pre-Deployment
[ ] Code changes are merged to main
[ ] Stage validation passed (all tests, SLOs)
[ ] Security scan complete (vulnerability report attached)
[ ] Changelog updated with v1.2.3
[ ] Runbooks/SRE docs updated for any new behavior
[ ] Load test passed (1000 req/sec sustained)

Approval
[ ] Engineering Manager approval: _______________
[ ] On-Call Lead approval: _______________
[ ] Ready for production: [ ] YES [ ] NO

Deployment Plan
Deployment Strategy: Rolling update with canary
  - Canary: 5% traffic to v1.2.3 (1 pod)
  - Monitor for 5 minutes
  - If SLO met: Proceed to 100%
  - If SLO missed: Rollback immediately

Expected duration: 10-15 minutes
Rollback command: git revert <commit>; git push origin main

Incident Contacts
  On-Call: alice@company.com
  Manager: bob@company.com
  CTO:     charlie@company.com

Signed: ______________  Date: ______________
```

### Production Deployment (Canary Strategy)

```bash
# 1. Create canary deployment (5% traffic)
kubectl set image deployment/billing-api \
  billing-api=ecps-billing-api:v1.2.3 \
  --record \
  -n team-alpha

# 2. Monitor canary for errors/latency
kubectl logs -f deployment/billing-api -n team-alpha --color=false | grep -i error
watch 'kubectl top pods -n team-alpha -l app=billing-api'

# 3. Check metrics in Prometheus
# - Error rate should remain < 0.1%
# - Latency p95 should remain < 500ms
# - Success rate should remain > 99.5%

# 4. If canary looks good, complete rollout
kubectl rollout resume deployment/billing-api -n team-alpha

# 5. Final verification
kubectl rollout status deployment/billing-api -n team-alpha --timeout=5m
```

### Disaster Recovery (Prod)

```bash
# If production incident occurs:

1. IMMEDIATE (0 min)
   - Page on-call engineer
   - Initiate incident response
   
2. FIRST 5 MINUTES
   - Gather diagnostics (logs, metrics)
   - Decide: Fix forward vs rollback?
   
3. ROLLBACK DECISION
   If unclear root cause → Rollback immediately
   
   git revert HEAD~1
   git push origin main
   kubectl rollout status deployment/billing-api

4. RESOLUTION VERIFICATION (5-10 min)
   - Confirm service is stable
   - Check SLOs are being met
   - Declare incident resolved
   
5. POST-MORTEM
   - Schedule post-mortem within 24 hours
   - Document timeline and actions
   - Implement preventative measures
```

---

## 🔄 Promotion Workflow

### Automated Promotion Pipeline

```
Developer
  │
  └─→ [1 hour] git push origin feature/xyz
      ↓
Dev Cluster
  │ Build + Deploy + Unit Tests
  │ (All pass? Continue)
  │
  └─→ [MANUAL: Engineer A approves]
      ↓
Stage Cluster
  │ Build + Deploy + Integration Tests + Load Tests + SLO Validation
  │ (All pass for 24 hours? Continue)
  │
  └─→ [MANUAL: Engg Manager reviews release notes + approves]
      ↓
Production Cluster
  │ Canary Deployment (5% traffic)
  │ (SLO met for 5 min? Continue)
  │
  └─→ Full Rollout to 100%
      │ Monitor for 1 hour (incident response ready)
      │
      └─→ Promotion Complete ✅
```

### Typical Timeline

```
Monday 10:00 AM
  Developer pushes feature to dev
  Automated deployment to dev cluster
  Manual testing in dev environment
  
Tuesday 9:00 AM
  Engineer approves for promotion to stage
  Automated deployment to stage
  24-hour validation window begins
  
Wednesday 9:00 AM
  Stage validation complete (all SLOs met)
  Change management review scheduled
  
Wednesday 2:00 PM
  Manager approves promotion to prod
  Canary deployment begins
  On-call engineer monitors
  
Wednesday 2:15 PM
  Canary metrics look good
  Full rollout begins
  
Wednesday 2:30 PM
  100% traffic on v1.2.3
  Post-deployment monitoring for 1 hour
  
Wednesday 3:30 PM
  Release declared successful ✅
  On-call released from monitoring
```

---

## 📊 Configuration Management

### How Environment Configs Are Maintained

```
infra/
├── envs/
│   ├── dev/
│   │   ├── main.tf           (Dev cluster config)
│   │   ├── namespaces.tf     (1x replica example)
│   │   ├── network-policies.tf (Loose policies)
│   │   └── values.yaml       (Lax settings)
│   │
│   ├── stage/
│   │   ├── main.tf           (Stage cluster config)
│   │   ├── namespaces.tf     (2x replica example)
│   │   ├── network-policies.tf (Strict policies)
│   │   └── values.yaml       (Production-like)
│   │
│   └── prod/
│       ├── main.tf           (Prod cluster config)
│       ├── namespaces.tf     (3x replica + PDB)
│       ├── network-policies.tf (Max strict)
│       └── values.yaml       (Maximum guards)

Principle:
- Shared base configs in infra/modules/
- Environment-specific overrides in infra/envs/{env}/
- Terraform uses variables to pass differences between environments
```

---

## ⚠️ Anti-Patterns (What NOT to Do)

### ❌ Single Environment ("Just Use Prod")
- **Problem**: No validation buffer, riskier, slower iteration
- **Solution**: Always have dev + stage

### ❌ Skipping Stage Testing ("We tested in dev")
- **Problem**: Dev != Prod (different config, load, data)
- **Solution**: Mandate stage validation for all releases

### ❌ Manual Promotion ("I'll SSH in and update...")
- **Problem**: Non-reproducible, audit trail is weak, error-prone
- **Solution**: All promotion via Git, automated pipelines

### ❌ Different Code per Environment ("Dev uses feature X, prod doesn't")
- **Problem**: Risk of deploying wrong version, harder to debug
- **Solution**: Same code everywhere, use flags or environment variables

### ❌ Ignoring SLOs in Dev ("Who cares about SLOs in dev")
- **Problem**: Careless dev practices don't prepare for prod discipline
- **Solution**: Same SLO checks everywhere (even if targets are relaxed)

---

## 📈 Monitoring Across Environments

### Environment-Specific Dashboards

**Dev Dashboard:**
- Deployment frequency (how often we deploy)
- Build success rate
- Test coverage
- Feature completion rate

**Stage Dashboard:**
- SLO attainment over 24-hour window
- Load test results (throughput, latency)
- Integration test pass rate
- Dependency compatibility

**Prod Dashboard:**
- SLO attainment (minute-by-minute)
- Error rate and latency
- Customer impact (failed transactions)
- On-call alert frequency

---

## 🎓 Learning from Environment Strategy

By implementing environment separation, ECPS demonstrates:

- ✅ **Risk management**: Validation gates between tiers
- ✅ **Operational discipline**: Controlled promotion workflows
- ✅ **Scalability thinking**: Separate concerns per environment
- ✅ **SRE principles**: SLO-driven deployment decisions
- ✅ **Change management**: Approval workflows and incident prevention

---

## 📚 Related Documents

- [SRE Playbook](./sre-playbook.md) – Incident response differs by environment
- [Architecture Overview](./architecture/README.md) – Environment design rationale
- [FinOps](./finops-notes.md) – Cost differences between environments

---

*Last updated: February 16, 2026*
