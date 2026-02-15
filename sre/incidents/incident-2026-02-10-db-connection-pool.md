# Incident: billing-api Database Connection Pool Exhaustion
**Date**: February 10, 2026, 14:32 UTC
**Duration**: 23 minutes (14:32-14:55 UTC)
**Severity**: P1 (Service Down)
**Post-Mortem Date**: February 10, 2026, 16:00 UTC

---

## Timeline

| Time | Event | Details |
|------|-------|---------|
| 14:32 | **P1 ALERT FIRED** | `billing_api_down` - Zero successful requests for 2+ minutes |
| 14:33 | **Acknowledge** | On-call engineer (Alice) acknowledges alert |
| 14:34 | **Investigation** | Check Grafana - Error rate 100%, all requests timeout |
| 14:35 | **Hypothesis** | Database likely unreachable (connection pool exhausted) |
| 14:36 | **Diagnostics** | `kubectl logs -f billing-api` → "connection pool exhausted" |
| 14:38 | **Root Cause Found** | PostgreSQL at 100% CPU, high lock wait times |
| 14:40 | **Mitigation Started** | Scale billing-api down to 1 replica (reduce connection demand) |
| 14:42 | **Partial Recovery** | Service partially responding, errors reducing |
| 14:45 | **Database Restart** | Restart PostgreSQL pod to clear locks |
| 14:47 | **Full Recovery** | All connections recovered, error rate dropping |
| 14:55 | **Stable** | SLO met, customer impact ceasing |
| 15:00 | **All Clear** | Metrics nominal, service declared recovered |

---

## Root Cause

**Primary Cause**: PostgreSQL connection pool exhaustion due to runaway background query

**Contributing Factors**:
1. **Connection pool limit too low** (20 connections)
   - Set when team was smaller
   - Should be 50-100 for current load

2. **Missing query timeout** (PostgreSQL config)
   - Long-running report query never completed
   - Held connections open indefinitely

3. **No alerting on DB connection utilization**
   - Alert would have fired hours before full exhaustion

---

## Customer Impact

- **Duration**: 23 minutes
- **Failed Requests**: ~3,500 failed invoice creations
- **Affected Customers**: 47 unique customers
- **Estimated Revenue Impact**: ~$1,200 in failed invoices
- **Affected SLO**: Availability dropped from 99.95% to 94%

---

## What We Did Right ✅

1. **Fast Detection**: AlertManager caught issue within 2 minutes
2. **Quick Diagnosis**: Connection pool exhaustion identified within 5 minutes
3. **Effective Mitigation**: Scaling down quickly reduced load on database
4. **Clear Communication**: Slack updates every 2-3 minutes

---

## What We Could Improve 🔧

| Issue | Fix | Owner | Timeline |
|-------|-----|-------|----------|
| No connection pool monitoring | Add `postgres_connections_used` to Prometheus | DBA Team | By Feb 12 |
| Connection pool limit hardcoded | Make configurable via ConfigMap | Backend Team | By Feb 12 |
| No query timeout in PostgreSQL | Set `statement_timeout = 5min` | DBA Team | By Feb 12 |
| No alert on pool utilization | Alert at 70% utilization | SRE Team | By Feb 13 |

---

## Action Items (Non-Blameless)

**Immediate (This Week)**
1. [ ] Increase PostgreSQL connection pool to 50
2. [ ] Add `statement_timeout` to PostgreSQL config
3. [ ] Add Prometheus alert for connection pool > 70%

**Short-term (This Month)**
4. [ ] Load test with current replica count to find bottlenecks
5. [ ] Document connection pool sizing logic
6. [ ] Add runbook: "Connection Pool Exhaustion"

**Long-term (This Quarter)**
7. [ ] Consider connection pooling proxy (pgBouncer)
8. [ ] Implement query performance monitoring (EXPLAIN ANALYZE)
9. [ ] Capacity planning: forecast when next upgrade needed

---

## Resolution

**Immediate Actions Taken**:
```bash
# Scale down to reduce connection demand
kubectl scale deployment billing-api --replicas=1 -n team-alpha

# Restart PostgreSQL to clear locks
kubectl delete pod postgres-xxxxx -n platform-data
kubectl wait --for=condition=ready pod -l app=postgres -n platform-data

# Scale back up
kubectl scale deployment billing-api --replicas=2 -n team-alpha (after DB stable)
```

**Permanent Fix**:
```yaml
# ConfigMap for PostgreSQL (WIP)
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
data:
  postgresql.conf: |
    max_connections = 100
    statement_timeout = 300000  # 5 minutes
    idle_in_transaction_session_timeout = 600000
```

---

## Learning

- Connection pools are a common bottleneck in high-throughput systems
- Lack of observability (no connection pool metrics) meant we were flying blind
- "It worked in dev" - load distribution is very different in practice
- Runaway queries are a silent killer - need query timeouts

---

**Post-Mortem Facilitator**: Charlie (Engineering Manager)  
**Participants**: Alice (On-Call), David (Database Engineer), Emma (Backend Lead)

---

