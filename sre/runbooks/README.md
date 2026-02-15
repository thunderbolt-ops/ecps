# SRE Runbooks - Troubleshooting Guide

This directory contains step-by-step runbooks for common operational issues in the ECPS platform.

## Quick Reference

| Issue | Service | Runbook | Severity |
|-------|---------|---------|----------|
| High error rate | billing-api, jobs-api | [Database Connection Errors](#database-connection-errors) | P1 |
| Job queue backing up | jobs-api, jobs-worker | [Job Queue Backup](#job-queue-backup) | P2 |
| Pods keep restarting | Any service | [Pod CrashLoopBackOff](#pod-crashloopbackoff) | P1 |
| Slow database queries | reporting-api, billing-api | [High Query Latency](#high-query-latency) | P2 |
| Jobs not processing | jobs-worker | [Jobs Not Processing](#jobs-not-processing) | P1 |
| Deadletter queue growing | jobs-worker | [Deadletter Queue Issues](#deadletter-queue-issues) | P2 |

---

## Database Connection Errors

**Symptoms:**
- High rate of DB_ERRORS counter in metrics
- Errors: "too many connections", "connection timeout"
- API latency spikes
- Services return 500 errors

**Root Causes:**
1. Connection pool exhausted (connections held open too long)
2. Database query hangs
3. Database pod restarting
4. Network connectivity issues

**Resolution Steps:**

### Step 1: Check current connections
```bash
kubectl exec -it pod/postgres-0 -n platform-data -- psql -U postgres -d postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"
```
- Max from app pool config: typically 10-20 per app
- PostgreSQL default max: 100
- **Issue if:** Current >> Max configured

### Step 2: Identify long-running queries
```bash
kubectl exec -it pod/postgres-0 -n platform-data -- psql -U postgres -d postgres -c \
  "SELECT pid, usename, state, query, query_start, now() - query_start as duration FROM pg_stat_activity \
   WHERE state != 'idle' ORDER BY duration DESC LIMIT 10;"
```
- **Action if found:** Kill the slow query with `SELECT pg_terminate_backend(pid)` if > 5 minutes

### Step 3: Check service pod logs
```bash
kubectl logs -n team-alpha deployment/billing-api -f | grep -i "connection\|error"
```
- Look for patterns: "pool exhausted", "connection refused", "timeout"

### Step 4: Verify database is healthy
```bash
kubectl get pods -n platform-data -l app=postgres
# Should show: 1 postgres pod Running
kubectl logs -n platform-data pod/postgres-0 | tail -50
```

### Step 5: Scale up connection pool (if needed)
Edit the problematic service deployment:
```bash
kubectl edit deployment SERVICE_NAME -n team-alpha
```
- Increase `replicationpool maxconn` in environment variables (e.g., `POOL_SIZE=20`)
- Scale down and up the deployment:
```bash
kubectl rollout restart deployment/SERVICE_NAME -n team-alpha
```

### Step 6: Monitor recovery
```bash
kubectl logs -n team-alpha deployment/SERVICE_NAME -f | grep -i "ready\|error"
watch -n 2 'kubectl top pods -n team-alpha'
```

**Expected resolution time:** 2-5 minutes

**Post-mortem notes:**
- Document the max connection count needed
- Update connection pool configuration in IaC
- Add connection pool monitoring alert if not present
- Consider query optimization if queries were slow

---

## Job Queue Backup

**Symptoms:**
- `jobs_api_queue_depth` metric > 100 and growing
- Job creation latency increasing
- Users report long wait times for job results

**Root Causes:**
1. jobs-worker pods not processing (hung, crashed, or restarting)
2. Insufficient jobs-worker replicas
3. Redis connectivity issues
4. Job processing blocked on slow database/MinIO operations

**Resolution Steps:**

### Step 1: Check jobs-worker pod status
```bash
kubectl get pods -n team-alpha -l app=jobs-worker
```
- All pods should show "Running" and "1/1 Ready"
- **If restarting:** Check logs: `kubectl logs -n team-alpha pod/jobs-worker-XXX --tail=50`

### Step 2: Check Redis connectivity
```bash
kubectl exec -it pod/redis-0 -n platform-data -- redis-cli info stats | grep total_commands
# Should show increasing number (worker is consuming)
```

### Step 3: Check job processing logs
```bash
kubectl logs -n team-alpha deployment/jobs-worker -f | head -100
# Look for: "Job picked up", "completed in", "ERROR"
```
- **If no "picked up" messages:** Worker isn't connecting to Redis
- **If "ERROR" messages:** Check deadletter queue

### Step 4: Scale up jobs-worker (temporary)
```bash
kubectl scale deployment jobs-worker -n team-alpha --replicas=4 # increase from default
```
- Monitor queue depth: `watch -n 5 'kubectl top pods -n team-alpha'`
- Workers should start consuming queue

### Step 5: Check for stuck jobs in deadletter queue
```bash
kubectl exec -it pod/redis-0 -n platform-data -- redis-cli LLEN jobs:deadletter
```
- **If > 0:** See [Deadletter Queue Issues](#deadletter-queue-issues)

### Step 6: Monitor until normal
```bash
watch -n 2 'kubectl logs -n team-alpha deployment/jobs-worker -f | tail -5'
# Should see "Job picked up" and "completed" messages regularly
```

**Expected resolution time:** 3-10 minutes

**Permanent fix:**
1. Increase default replicas in deployment.yaml
2. Add HorizontalPodAutoscaler based on queue depth
3. Optimize slowest job types

---

## Pod CrashLoopBackOff

**Symptoms:**
- Pod shows "CrashLoopBackOff" status
- Restarts every 10-20 seconds
- No endpoints available

**Root Causes:**
1. Application crash (unhandled exception)
2. Missing environment variables
3. Configuration/secret not mounted
4. Insufficient resource requests
5. Health check timeout

**Resolution Steps:**

### Step 1: Get crash logs
```bash
kubectl logs -n team-alpha pod/POD_NAME --previous
# Get most recent crash dump
```

### Step 2: Identify the issue
- **"RuntimeError: DB_NAME must be set":** Missing environment variables
- **"psycopg2.OperationalError: could not connect":** Database connectivity
- **"OutOfMemory":** Insufficient memory request
- **"readiness probe failed":** Health check not responding

### Step 3: Fix based on issue type

**Database credentials missing:**
```bash
kubectl edit deployment SERVICE_NAME -n team-alpha
# Verify env vars: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD are set
kubectl rollout restart deployment/SERVICE_NAME -n team-alpha
```

**Database unreachable:**
```bash
# Check if postgres pod is running
kubectl get pods -n platform-data -l app=postgres
# Verify cluster network policies aren't blocking traffic
```

**Insufficient resources:**
```bash
kubectl edit deployment SERVICE_NAME -n team-alpha
# Increase resources.requests.memory from 128Mi to 256Mi
kubectl rollout restart deployment/SERVICE_NAME -n team-alpha
```

**Health check failing:**
```bash
kubectl describe pod -n team-alpha POD_NAME | grep "Readiness\|Liveness"
# Check the probe: httpGet path, initial delay, timeout
# If timeout too aggressive (e.g., 1s), increase to 5s
kubectl edit deployment SERVICE_NAME -n team-alpha
```

### Step 4: Verify recovery
```bash
kubectl get pods -n team-alpha -l app=SERVICE_NAME
# Should show "1/1 Ready"
kubectl logs pod/POD_NAME -n team-alpha -f | head -20
```

**Expected resolution time:** 2-5 minutes

---

## High Query Latency

**Symptoms:**
- `reporting_api_request_latency_seconds` p95 > 500ms
- High CPU on postgres pod
- Users report slow report loading

**Root Causes:**
1. Missing database indexes
2. Complex JOIN queries on large tables
3. Concurrent high-load queries
4. Database resource contention

**Resolution Steps:**

### Step 1: Check slow query log
```bash
kubectl exec -it pod/postgres-0 -n platform-data -- psql -U postgres -d billing -c \
  "SELECT query, mean_exec_time, calls FROM pg_stat_statements \
   ORDER BY mean_exec_time DESC LIMIT 10;" 2>/dev/null || echo "Need to enable pg_stat_statements"
```

### Step 2: Analyze expensive query plans
```bash
# Example: Replace QUERY_TEXT with actual slow query
kubectl exec -it pod/postgres-0 -n platform-data -- psql -U postgres -d billing -c \
  "EXPLAIN ANALYZE QUERY_TEXT;"
```
- Look for "Seq Scan" on large tables (should be "Index Scan")
- Look for high "Actual rows" vs "Planned rows" (stale statistics)

### Step 3: Add missing indexes
```bash
kubectl exec -it pod/postgres-0 -n platform-data -- psql -U postgres -d billing -c \
  "CREATE INDEX idx_usage_records_team_ts ON usage_records(team, ts DESC) WHERE status = 'active';"
```
- Recommend indexes for columns used in WHERE, JOIN, ORDER BY

### Step 4: Update statistics
```bash
kubectl exec -it pod/postgres-0 -n platform-data -- psql -U postgres -d billing -c \
  "ANALYZE usage_records; ANALYZE invoices; ANALYZE jobs;"
```

### Step 5: Monitor latency improvement
```bash
watch -n 2 'kubectl logs -n team-alpha deployment/reporting-api -f | tail -3'
# Latency should decrease in new requests
```

**Expected resolution time:** 5-15 minutes

**Permanent fix:**
1. Add recommended indexes to database initialization SQL
2. Schedule ANALYZE on schedule (weekly)
3. Consider partitioning if table is >100MB

---

## Jobs Not Processing

**Symptoms:**
- `jobs_worker_jobs_processed_total` not increasing
- Queue has jobs but nothing is consumed
- Jobs stuck in "queued" status

**Root Causes:**
1. jobs-worker pod not running
2. Redis connection broken
3. Database connection pool exhausted
4. Worker process hung (deadlock)

**Resolution Steps:**

###Step 1: Check jobs-worker state
```bash
kubectl get deployment -n team-alpha jobs-worker -o yaml | grep -A 5 "selector:"
kubectl get pods -n team-alpha -l app=jobs-worker
```
- Should have at least 1 pod in "Running" state
- If 0 replicas: `kubectl scale deployment jobs-worker --replicas=1`

### Step 2: Check Redis connectivity
```bash
kubectl exec -it pod/jobs-worker-XXX -n team-alpha -- redis-cli ping
# Should return PONG
```

### Step 3: Check worker logs for blockers
```bash
kubectl logs -n team-alpha deployment/jobs-worker -f | tail -50
# Look for: "ERROR", "connection", "timeout", "pool exhausted"
```

### Step 4: Force restart worker pod
```bash
kubectl delete pod -n team-alpha -l app=jobs-worker
# New pod will start automatically
sleep 10
kubectl logs -n team-alpha deployment/jobs-worker -f | head -20
# Should see "jobs-worker starting up"
```

### Step 5: Monitor processing resume
```bash
watch -n 2 'kubectl logs -n team-alpha deployment/jobs-worker -f | tail -1'
# Should see "Job picked up" and "completed"
```

**Expected resolution time:** 2-5 minutes

---

## Deadletter Queue Issues

**Symptoms:**
- `jobs_worker_deadletter_queue_depth` > 0
- Alert "Jobs in deadletter queue detected"
- Jobs never reach "completed" status

**Root Causes:**
1. Jobs retried MAX_RETRIES times and still failing
2. Unsupported job type
3. Database/MinIO issue that persists across retries
4. Invalid job parameters

**Resolution Steps:**

### Step 1: Examine deadletter queue
```bash
kubectl exec -it pod/redis-0 -n platform-data -- redis-cli LRANGE jobs:deadletter 0 -1 | head -1 | jq .
```

### Step 2: Analyze job failure reason
```bash
# In the job JSON, look for "parameters.error" field
# This shows what happened on last retry
```

**Common failures:**
- "Unsupported job_type": Job type not recognized → Implement handler or reject job
- "Table does not exist": Schema missing → Run migrations
- "Access denied": MinIO permissions → Fix bucket ACLs or credentials
- "Connection refused": Database/Redis down → Check service health

### Step 3: Manual recovery (case-by-case)

**If job type unsupported:**
- Don't retry, contact job submitter, manually delete from deadletter queue

**If infrastructure issue (resolved now):**
```bash
# Manually move job back from deadletter to main queue for retry
kubectl exec -it pod/redis-0 -n platform-data -- redis-cli RPOPLPUSH jobs:deadletter jobs:queue
```

**If job parameters invalid:**
- Delete from deadletter queue, no action needed
```bash
kubectl exec -it pod/redis-0 -n platform-data -- redis-cli LPOP jobs:deadletter
```

### Step 4: Clear deadletter queue once recovered
```bash
kubectl exec -it pod/redis-0 -n platform-data -- redis-cli DEL jobs:deadletter
```

### Step 5: Post-incident review
Document what caused the job failure and implement fixes:
- Add validation to jobs-api for job parameters
- Add better error messages for support teams
- Monitor retry failure patterns to catch systemic issues early

**Expected resolution time:** 10-30 minutes (depends on root cause)

---

## General Debugging Tips

### Check all pod statuses
```bash
kubectl get pods -n team-alpha --show-labels
kubectl get pods -n platform-data --show-labels
```

### Stream logs from multiple pods
```bash
kubectl logs -n team-alpha deployment/billing-api -f --all-containers --timestamps=true | grep -i error
```

### Get resource usage
```bash
kubectl top pods -n team-alpha
kubectl top nodes
# Watch memory: usually the first constraint in dev
```

### Check configured alerts
```bash
kubectl get prometheusrule -n platform-observability
kubectl get alertmanagerrule -n platform-observability  # if configured
```

### Access Prometheus directly
```bash
kubectl port-forward -n platform-observability svc/kube-prometheus-stack-prometheus 9090:9090 &
# Visit http://localhost:9090
```

### Access Grafana dashboards
```bash
kubectl port-forward -n platform-observability svc/kube-prometheus-stack-grafana 3000:80 &
# Visit http://localhost:3000 (default: admin/prom-operator)
```

---

## Escalation Path

1. **First 5 minutes:** Use runbooks above to triage and attempt fixes
2. **5-15 minutes:** If unresolved, check platform logs and metrics on Prometheus/Grafana
3. **15+ minutes:** Page on-call platform engineer (see SRE playbook for escalation chain)
4. **During incident:** Post updates to #incident Slack channel
5. **After resolution:** Schedule post-mortem within 24 hours

---

## Contact & Resources

- **SRE Playbook:** [docs/sre-playbook.md](../sre-playbook.md)
- **Architecture:** [docs/architecture/](../architecture/)
- **ADRs:** [docs/adr/](../adr/)
- **Incident Tracker:** [sre/incidents/](../incidents/)
