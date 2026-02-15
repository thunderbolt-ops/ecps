# SRE Playbook

**How to operate, monitor, and respond to incidents on ECPS.**

This playbook defines:
- Service Level Objectives (SLOs) and error budgets
- Alert thresholds and on-call escalation
- Incident response procedures
- Post-mortem process
- Runbook references

---

## 🎯 Service Level Objectives (SLOs)

### Definition

An SLO is a measurable target for service behavior:
- **Availability SLO**: 99.5% availability = 3.6 hours downtime per month
- **Latency SLO**: 95th percentile latency < 500ms
- **Success SLO**: < 0.1% error rate

### ECPS Services

#### billing-api

| SLI | Target | Error Budget |
|-----|--------|--------------|
| **Availability** | 99.5% | 3.6 hours/month |
| **Latency (p95)** | < 500ms | Burn tracked independently |
| **Errors** | < 0.1% | 360 errors/month (on 4M RPS baseline) |

- **Critical Transactions**: Invoice creation, usage recording
- **Measurement Window**: Rolling 30-day month
- **Error Budget Consumption**: Tracked per PrometheusRule

#### reporting-api

| SLI | Target | Error Budget |
|-----|--------|--------------|
| **Availability** | 99.5% | 3.6 hours/month |
| **Latency (p95)** | < 1000ms | Burn tracked independently |
| **Errors** | < 0.1% | 360 errors/month (baseline) |

- **Critical Transactions**: Report generation, data aggregation
- **Measurement Window**: Rolling 30-day month

#### hello-app

| SLI | Target | Error Budget |
|-----|--------|--------------|
| **Availability** | 99.9% | 43 minutes/month |
| **Latency (p95)** | < 100ms | Burn tracked independently |

- **Simple service with no critical transactions**
- **Used for platform self-test and smoke testing**

### Error Budget Policy

**When budget is consumed:**

| Consumption | Action |
|-------------|--------|
| <10% | No action required |
| 10-50% | Monitor closely, prepare for degradation |
| 50-75% | Page on-call, discuss scaling or fixes |
| 75-90% | Freeze new feature deployments, focus on reliability |
| >90% | Only bug fixes and critical patches allowed |

---

## 🚨 Alerting & On-Call

### Alert Priorities

#### P1 (Page On-Call Immediately)

- **Service completely unavailable** (0% success rate for >5 minutes)
- **All replicas down** for critical service
- **Database unreachable** (impacts all dependent services)
- **Cluster control plane issues** (affects all workloads)

**Example alerts:**
```
ALERTS firing:
- billing_api_down (no successful responses)
- database_unavailable
- cluster_unhealthy
```

**Response time**: 5 minutes

#### P2 (Notify On-Call, Not Urgent Page)

- **Degraded service** (success rate 50-99%)
- **Latency SLO breach** but requests succeeding
- **Error budget burning fast** (>10% per hour)
- **High error rate** but some requests succeeding (>1% errors)

**Example alerts:**
```
ALERTS firing:
- billing_api_latency_high
- error_budget_burn_rate_high
- pod_restart_loop
```

**Response time**: 15 minutes

#### P3 (Informational)

- **Minor latency increase** (<10% over baseline)
- **Single pod restart** (replicas still healthy)
- **Operational warnings** (disk usage at 70%)

**Example alerts:**
```
ALERTS:
- high_memory_usage_approaching
- disk_usage_warning
```

**Response time**: Next business day

### Alert Channels

1. **P1 Alerts**: SMS + Slack + Email (escalate every 5 min)
2. **P2 Alerts**: Slack channel + Email notification
3. **P3 Alerts**: Slack channel (informational)

---

## 📋 Incident Response Procedure

### Phase 1: Detection & Triage (First 5 minutes)

**Trigger**: P1 or P2 alert fires

**On-call steps:**
1. Acknowledge alert in monitoring system
2. Open Grafana dashboard for affected service
3. Check recent deployments (last 30 minutes)
4. Note in Slack: `Incident: billing-api degraded - investigating`

**Diagnosis questions:**
- When did this start? (correlate with time)
- Are metrics available? (check Prometheus)
- Did anything change? (check deployment history)
- Is the cluster healthy? (check node status, pod status)

### Phase 2: Initial Response (Next 5-15 minutes)

**If clear root cause:**
- Execute relevant runbook (see below)
- Document actions in Slack thread
- Monitor metrics for recovery

**If root cause unclear:**
- Escalate to on-call lead
- Page backup on-call engineer if P1
- Start collecting logs and traces
- Consider service degradation or failover
- Notify stakeholders (especially for P1)

### Phase 3: Resolution (Next 15-60 minutes)

**Once resolved:**
1. Verify service health (metrics, test endpoints)
2. Document root cause and resolution in Slack
3. Calculate impact (duration × customer impact)
4. Prepare for post-mortem if P1

---

## 📚 Common Runbooks

### runbook: Database Connection Errors

**Symptoms:**
- Alerts: `billing_api_db_errors_total` increasing
- Logs: "connection refused" or "connection timeout"

**Investigation:**
```bash
# Check PostgreSQL pod status
kubectl get pods -n platform-data -l app=postgres

# Check PostgreSQL logs
kubectl logs -n platform-data deployment/postgres
```

**Resolution:**
```bash
# 1. Verify database is running
kubectl get svc postgres -n platform-data

# 2. Test connectivity from app pod
kubectl exec -it -n team-alpha <pod> -- \
  pg_isready -h postgres.platform-data.svc.cluster.local -p 5432

# 3. If DB unreachable, restart PostgreSQL
kubectl rollout restart deployment/postgres -n platform-data

# 4. Wait for DB to stabilize
kubectl wait --for=condition=ready pod \
  -l app=postgres -n platform-data --timeout=300s
```

**Prevention:**
- Set resource requests/limits on Postgres
- Enable pod disruption budgets (PDB)
- Monitor database connection pool

---

### runbook: High Error Rate

**Symptoms:**
- Alert: `billing_api_request_error_rate_high` (>1%)
- Grafana: Error rate spike on service dashboard

**Investigation:**
```bash
# 1. Check recent deployments
kubectl rollout history deployment/billing-api -n team-alpha

# 2. Check pod logs
kubectl logs -n team-alpha -l app=billing-api --tail=100

# 3. Check for pod crashes
kubectl describe pod <pod-name> -n team-alpha | grep -A5 "Last State"

# 4. Check if resource-constrained
kubectl top pods -n team-alpha -l app=billing-api
```

**Common causes & fixes:**
- **Database unreachable**: See database runbook above
- **Memory pressure**: Increase resource limits or reduce replicas
- **Invalid config**: Check ConfigMaps and Secrets
- **Bad deployment**: Run `kubectl rollout undo`

---

### runbook: Pod CrashLoopBackOff

**Symptoms:**
- Pod status: `CrashLoopBackOff`
- Alert: `pod_crash_loop_backoff` firing

**Investigation:**
```bash
# 1. Check pod logs (from current and previous container)
kubectl logs <pod-name> -n team-alpha --previous

# 2. Check pod events
kubectl describe pod <pod-name> -n team-alpha

# 3. Check exit code and reason
kubectl get pod <pod-name> -n team-alpha -o yaml | grep -A5 "lastState"
```

**Common causes:**
- **Config not mounted**: Check ConfigMap/Secret exists
- **Env var missing**: Check deployment spec
- **Resource exhaustion**: Pod OOMKilled
- **Application bug**: Check code and recent deployments

**Resolution:**
```bash
# Option 1: Fix and redeploy (preferred)
# Update code/config, commit to Git, let ArgoCD sync

# Option 2: Scale down failing deployment
kubectl scale deployment billing-api --replicas=0 -n team-alpha
# Wait for investigation, then restore
kubectl scale deployment billing-api --replicas=2 -n team-alpha
```

---

### runbook: Network Connectivity Issues

**Symptoms:**
- Service A can't reach Service B
- Network policy violation? Check:

```bash
# 1. Check if pods can reach each other
kubectl exec -it <pod-a> -n team-alpha -- \
  ping <pod-b>.team-alpha.svc.cluster.local

# 2. Check NetworkPolicies in place
kubectl get networkpolicies -n team-alpha
kubectl describe networkpolicy <policy-name> -n team-alpha

# 3. Check DNS
kubectl exec -it <pod> -n team-alpha -- \
  nslookup billing-api.team-alpha.svc.cluster.local
```

**Resolution:**
- Update NetworkPolicy to allow communication
- Document the change in an ADR
- Test before and after policy changes

---

## 🎓 Post-Mortem Process

### When to Do a Post-Mortem

- **P1 incidents**: Always
- **P2 incidents**: If user-facing impact or duration >30 min
- **Learning opportunities**: Even if low-severity if valuable lesson

### Post-Mortem Template

```markdown
# Post-Mortem: [Service Name] Incident on [Date]

## Context
- **Duration**: HH:MM - HH:MM (NN minutes total downtime)
- **Services Affected**: billing-api, reporting-api
- **Customer Impact**: N invoices failed to process
- **Severity**: P1 / P2 / P3

## Timeline
- **HH:MM** - Alert: Database connection errors detected
- **HH:MM** - Acknowledged by on-call engineer
- **HH:MM** - Root cause identified: PostgreSQL restarted
- **HH:MM** - Service recovered, all systems nominal
- **HH:MM** - Post-mortem started

## Root Cause
PostgreSQL pod was evicted due to OOMKilled. The memory limit
was set too low for the upgraded schema migration.

## Contributing Factors
1. Memory limit not updated when schema was upgraded
2. No pre-deployment load testing
3. No liveness probe restart (waited for manual intervention)

## Impact
- 15 minutes of 100% error rate for billing-api
- ~1,500 invoice creation requests failed
- User-facing impact: Users saw "Service Unavailable"

## Resolution
Immediately scaled down billing-api replicas to reduce memory pressure.
Restarted PostgreSQL with increased memory limit (from 512Mi to 2Gi).
Services recovered within 2 minutes.

## Action Items (Blameless)
1. **[Done]** Increase PostgreSQL memory limit to 2Gi
2. **[In Progress]** Add pre-deployment load test for schema changes
3. **[Scheduled]** Review all service memory limits vs current usage
4. **[Future]** Implement liveness probe for faster recovery

## Timeline for Fixes
- Memory limit: Deployed immediately
- Load testing: Complete by end of sprint
- Memory audit: Complete within 2 weeks
- Liveness probe: Include in next release

## Lessons Learned
- Always test memory usage change with production-like data
- Memory limits need to account for migration peaks
- Consider faster automatic recovery mechanisms
```

### Blameless Culture

**Remember:**
- No individual names in incident reports
- Focus on systemic issues, not personal failures
- Questions: "What conditions led to this?" not "Who broke this?"
- Goal: Prevent recurrence, not punishment

---

## 👥 On-Call Responsibilities

### Primary On-Call
- Responds to all P1 and P2 alerts within SLA
- Makes decisions to mitigate (rollback, scale, failover)
- Communicates status to stakeholders
- Starts incident response process
- Documents incident for post-mortem
- Completes runbooks and action items

### On-Call Backup
- Monitors same channels, backs up primary
- Takes over if primary unreachable >10 minutes
- Shares context before transition
- Available for escalations

### On-Call Lead
- Supervises multiple services
- Escalation point for complex issues
- Makes critical decisions (scale infrastructure, page architects)
- Post-mortem facilitation

---

## 📊 Monitoring & Dashboards

### Primary Dashboard

**Location**: Grafana (http://localhost:3000 after port-forward)

**Panels:**
- **Service Health**: Success rate, latency (p50, p95, p99)
- **Error Budget**: Hours remaining this month
- **Resource Usage**: CPU, memory, disk across all pods
- **Alert Status**: Active alerts, firing rules
- **Deployment History**: Recent deploys and their impact

### How to Use in Incident Response

1. **Confirm service is degraded**: Check success rate and latency
2. **Understand scope**: Which service? Which region/zone?
3. **Find correlation**: Did error rate spike match a deploy?
4. **Track recovery**: Watch metrics return to normal
5. **Measure impact**: Integrate error rate over incident duration

---

## 🔄 Continuous Reliability Improvements

### Weekly Reviews

Every Thursday, review:
- Alert storms (false positives)
- Alert gaps (missed P1s)
- On-call experience (pain points)
- Runbook effectiveness (outdated?)

### Monthly Reviews

Every last Friday, review:
- SLO attainment (on track?)
- Error budget burndown (normal pace?)
- Top incidents (learn from trends)
- Capacity projections (growth trajectory)

### Quarterly Reviews

Every quarter, review:
- Architecture changes needed
- Reliability investment ROI
- Training and knowledge gaps
- Tool and process improvements

---

## 📞 Contacts & Escalation

### On-Call Rotation

```
Week 1-2:   Engineer A (Primary), Engineer B (Backup)
Week 3-4:   Engineer C (Primary), Engineer D (Backup)
Week 5-6:   Engineer E (Primary), Engineer F (Backup)
...
```

**Handoff**: Friday end-of-day, sync on recent incidents

### Escalation Chain

1. **Primary On-Call** (0-10 min)
2. **Backup On-Call** (10-20 min if primary unreachable)
3. **On-Call Lead** (20+ min, complex issues)
4. **Engineering Manager** (major outages, communications)
5. **Technical Architect** (design-level decisions)

---

## ✅ SRE Excellence Goals

By following this playbook, ECPS SREs will:

- ✅ Respond to incidents in <5 minutes
- ✅ Resolve most incidents in <15 minutes
- ✅ Achieve 99.5% service availability
- ✅ Maintain detailed incident records
- ✅ Share knowledge through runbooks
- ✅ Continuously improve without blame
- ✅ Support on-call wellness and rotation

---

## 📖 Related Documents

- [Runbooks](./runbooks/) – Step-by-step incident response guides
- [Incidents](./incidents/) – Past incidents and post-mortems
- [SLOs](./slos/) – Detailed SLO definitions per service
- [Dashboards](./dashboards/) – Grafana dashboard definitions

---

*Last updated: February 16, 2026*
