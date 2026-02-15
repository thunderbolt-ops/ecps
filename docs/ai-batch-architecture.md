# AI & Batch Workload Architecture

**How ECPS handles batch jobs and AI/ML-style asynchronous workloads.**

This document covers:
- Batch job submission and processing
- Queue-based job distribution
- Node labeling and pod scheduling
- Resource isolation for compute-heavy workloads
- Observability for batch systems

---

## 🎯 Use Case

**Problem**: Some workloads are not interactive APIs:
- Analytics reports (long-running, batch)
- Statistical analysis (compute-heavy)
- Data simulations (need GPU acceleration)
- Machine learning inference (expensive compute)

**Solution**: Separate job submission (fast API) from job processing (background workers)

**Benefits:**
- User gets immediate response (job queued)
- Processing happens asynchronously in background
- Workers auto-scale based on queue depth
- Expensive (GPU) compute isolated on labeled nodes

---

## 🏗️ Architecture

### Components

```
┌──────────────┐
│  Client App  │  (Web UI or external service)
└──────┬───────┘
       │ HTTP POST /api/v1/jobs
       ↓
┌──────────────────────┐
│  jobs-api Service    │  (team-alpha)
│ - Accepts submissions│
│ - Stores in DB       │
│ - Returns job ID     │
│ - Status endpoint    │
└──────┬───────────────┘
       │ INSERT into postgres.jobs
       ↓
┌────────────────────┐
│  PostgreSQL (Shared)  │
│  - jobs table      │
│  - job_status,     │
│    job_type, etc   │
└────────┬───────────┘
         │ Queue: SELECT * WHERE status='queued'
         ↓
┌──────────────────────┐
│  jobs-worker Instance 1 │ (Container)
│  - Polls queue       │
│  - Acquires job      │
│  - Processes work    │
│  - Updates status    │
└──────────────────────┘

                    ┌──────────────────────┐
                    │  jobs-worker Instance N │ (Parallel)
                    │  - Same queue logic   │
                    │  - N workers in pool  │
                    └──────────────────────┘
```

### Data Flow

```
1. User submits job
   POST /api/v1/jobs
   {"type": "analytics", "params": {...}}
   
2. jobs-api stores job record
   INSERT INTO jobs (id, type, status, params, created_at)
   VALUES ('job-12345', 'analytics', 'queued', {...}, now())
   Returns: {"id": "job-12345", "status": "queued"}

3. User checks status
   GET /api/v1/jobs/job-12345
   Returns: {"id": "job-12345", "status": "queued", ...}

4. jobs-worker instance polls queue
   SELECT * FROM jobs WHERE status='queued' LIMIT 1
   UPDATE jobs SET status='running', started_at=now()
   
5. Worker processes job
   - Run compute-intensive algorithm
   - Generate results
   - Store results in MinIO (S3-like)
   
6. Worker updates completion
   UPDATE jobs SET status='completed', completed_at=now(), result_s3_path=...
   
7. User checks result
   GET /api/v1/jobs/job-12345
   Returns: {"status": "completed", "result_url": "s3://...", ...}
```

---

## 🗂️ Data Model

### jobs_table

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,           -- 'analytics', 'ml_inference', etc.
    status VARCHAR(20) NOT NULL,         -- 'queued', 'running', 'completed', 'failed'
    
    -- Input parameters (JSON, flexible)
    params JSONB NOT NULL,               -- {"start_date": "2026-01-01", ...}
    
    -- Timing
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Result and error info
    result_s3_path TEXT,                 -- e3://minio/results/job-12345.json
    error_message TEXT,                  -- If failed
    
    -- Metadata
    submitted_by VARCHAR(100),           -- User or service
    priority INT DEFAULT 1,              -- 1=normal, 2=high, 3=critical
    retries INT DEFAULT 0,
    
    INDEX idx_status(status),            -- Speed up polling
    INDEX idx_type(type),
    INDEX idx_created(created_at)
);
```

### Example Records

```sql
-- Queued job
INSERT INTO jobs (id, type, status, params, created_at, priority)
VALUES (
    'job-001',
    'analytics_report',
    'queued',
    '{"days": 7, "metric": "invoice_count"}',
    NOW(),
    2  -- High priority
);

-- Running job
UPDATE jobs
SET status='running', started_at=NOW()
WHERE id='job-001';

-- Completed job
UPDATE jobs
SET status='completed', 
    completed_at=NOW(),
    result_s3_path='s3://results/analytics_report_001.json'
WHERE id='job-001';
```

---

## 🖥️ jobs-api Service

### Responsibilties

1. **Accept job submissions**
   ```http
   POST /api/v1/jobs
   Content-Type: application/json
   
   {
     "type": "analytics_report",
     "params": {
       "start_date": "2026-01-01",
       "end_date": "2026-01-07",
       "metric": "invoice_count"
     }
   }
   ```

2. **Return job ID immediately**
   ```json
   {
     "id": "job-12345",
     "status": "queued",
     "estimated_wait_seconds": 45
   }
   ```

3. **Provide status endpoint**
   ```http
   GET /api/v1/jobs/{job_id}
   ```
   Returns current status and progress

4. **List user's jobs**
   ```http
   GET /api/v1/jobs?user=alice&status=completed
   ```
   Returns paginated list with filters

### Implementation Snippet

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import os

app = FastAPI(title="Jobs API")

class JobRequest(BaseModel):
    type: str
    params: dict

class JobResponse(BaseModel):
    id: str
    status: str
    created_at: str
    
@app.post("/api/v1/jobs", response_model=JobResponse)
def submit_job(req: JobRequest):
    # Validate job type
    valid_types = ["analytics_report", "ml_inference", "data_simulation"]
    if req.type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid job type")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Store in database
    conn = get_db()
    conn.execute(
        "INSERT INTO jobs (id, type, status, params, created_at) VALUES (%s, %s, %s, %s, NOW())",
        (job_id, req.type, "queued", json.dumps(req.params))
    )
    conn.commit()
    
    return JobResponse(
        id=job_id,
        status="queued",
        created_at=datetime.now().isoformat()
    )

@app.get("/api/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    conn = get_db()
    result = conn.execute(
        "SELECT id, type, status, result_s3_path, error_message FROM jobs WHERE id=%s",
        (job_id,)
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": result[0],
        "type": result[1],
        "status": result[2],
        "result_url": result[3],
        "error": result[4]
    }
```

---

## ⚙️ jobs-worker Service

### Responsibilities

1. **Poll the job queue** (every 1-5 seconds)
   ```sql
   SELECT * FROM jobs WHERE status='queued' ORDER BY priority DESC, created_at ASC LIMIT 1
   ```

2. **Lock the job** (atomic acquire)
   ```sql
   UPDATE jobs SET status='running', started_at=NOW() WHERE id=%s
   ```

3. **Process the job**
   - Execute job-type-specific logic
   - Handle errors gracefully
   - Stream results as they're computed

4. **Store results**
   - Upload to MinIO/S3
   - Update job status in DB

5. **Handle failures**
   - Retry with exponential backoff
   - Log errors for debugging
   - Notify if max retries exceeded

### Implementation Snippet

```python
import time
import json
import os
from datetime import datetime
import psycopg2
import boto3

# Connect to S3 (MinIO)
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('S3_ENDPOINT'),
    access_key_id=os.getenv('S3_ACCESS_KEY'),
    secret_access_key=os.getenv('S3_SECRET_KEY')
)

def poll_and_process_jobs():
    """Main worker loop - runs continuously"""
    while True:
        try:
            # Poll for next job
            job = acquire_next_job()
            if not job:
                time.sleep(5)  # No jobs, wait and try again
                continue
            
            # Process the job
            result = process_job(job)
            
            # Store result and mark as complete
            store_result(job['id'], result)
            mark_completed(job['id'])
            
        except Exception as e:
            # Handle errors, retry, etc.
            logger.error(f"Job processing failed: {e}")
            handle_failure(job['id'], str(e))

def acquire_next_job():
    """Atomically get next queued job"""
    conn = get_db()
    try:
        conn.execute("BEGIN")
        
        # Lock the row for update
        job = conn.execute(
            """
            SELECT * FROM jobs 
            WHERE status='queued' 
            ORDER BY priority DESC, created_at ASC 
            LIMIT 1 FOR UPDATE
            """,
        ).fetchone()
        
        if job:
            # Transition to running
            conn.execute(
                "UPDATE jobs SET status='running', started_at=NOW() WHERE id=%s",
                (job['id'],)
            )
            conn.commit()
        else:
            conn.commit()
        
        return job
    except Exception as e:
        conn.rollback()
        raise

def process_job(job):
    """Execute job-specific logic"""
    job_type = job['type']
    params = json.loads(job['params'])
    
    if job_type == 'analytics_report':
        return generate_analytics_report(params)
    elif job_type == 'ml_inference':
        return run_ml_model(params)
    elif job_type == 'data_simulation':
        return run_simulation(params)
    else:
        raise ValueError(f"Unknown job type: {job_type}")

def generate_analytics_report(params):
    """Example: Generate analytics report"""
    start_date = params['start_date']
    days = params.get('days', 7)
    
    # Query database for data
    conn = get_db()
    data = conn.execute(
        """
        SELECT COUNT(*) as invoice_count
        FROM invoices
        WHERE created_at >= %s AND created_at < %s + INTERVAL '1 day'
        """,
        (start_date, start_date)
    ).fetchone()
    
    # Generate report
    report = {
        "period": start_date,
        "invoice_count": data['invoice_count'],
        "generated_at": datetime.now().isoformat()
    }
    
    return report

def store_result(job_id, result):
    """Upload result to S3/MinIO"""
    s3_key = f"job-results/{job_id}.json"
    s3_client.put_object(
        Bucket='results',
        Key=s3_key,
        Body=json.dumps(result),
        ContentType='application/json'
    )
    return f"s3://results/{s3_key}"

def mark_completed(job_id):
    """Update job status in database"""
    conn = get_db()
    result_path = store_result(job_id, result)
    conn.execute(
        """
        UPDATE jobs 
        SET status='completed', completed_at=NOW(), result_s3_path=%s 
        WHERE id=%s
        """,
        (result_path, job_id)
    )
    conn.commit()

if __name__ == '__main__':
    poll_and_process_jobs()
```

---

## 🎯 Pod Scheduling & Node Affinity

### Node Labels

Kubernetes nodes are labeled to indicate their capabilities:

```yaml
# Standard compute nodes
Labels:
  node-type: standard
  cpu: x86
  
# GPU nodes (simulated)
Labels:
  node-type: gpu
  gpu: true
  cpu: x86-gpu
```

### Pod Scheduling

**Standard jobs** (analytics, reporting):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jobs-api
spec:
  template:
    spec:
      nodeSelector:
        node-type: standard  # Run on standard nodes
      containers:
      - name: api
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
```

**GPU jobs** (intensive processing):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jobs-worker
spec:
  template:
    spec:
      nodeSelector:
        node-type: gpu  # Run on GPU nodes
      containers:
      - name: worker
        resources:
          requests:
            cpu: 2000m        # Full core for compute
            memory: 2Gi       # More memory for processing
```

### Example: Scaling Workers by Queue Depth

```bash
# Check queue length
QUEUE_DEPTH=$(kubectl exec -it deployment/postgres -n platform-data -- \
  psql -U postgres -c "SELECT COUNT(*) FROM jobs WHERE status='queued'")

# Auto-scale workers based on queue
if [ $QUEUE_DEPTH -gt 10 ]; then
  kubectl scale deployment jobs-worker --replicas=4 -n team-alpha
elif [ $QUEUE_DEPTH -gt 5 ]; then
  kubectl scale deployment jobs-worker --replicas=2 -n team-alpha
else
  kubectl scale deployment jobs-worker --replicas=1 -n team-alpha
fi
```

---

## 📊 Observability

### Metrics

Applications expose job-related metrics:

```prometheus
# Job submission rate
jobs_api_submissions_total{job_type="analytics", status="accepted"}
jobs_api_submissions_total{job_type="ml_inference", status="invalid"}

# Job processing metrics
jobs_worker_processing_duration_seconds{job_type="analytics"}
jobs_worker_processing_duration_seconds{job_type="ml_inference"}

# Queue depth
jobs_queue_depth{status="queued"}
jobs_queue_depth{status="running"}
jobs_queue_depth{status="completed"}

# Job success/failure
jobs_completed_total{status="success", job_type="analytics"}
jobs_completed_total{status="failure", job_type="analytics"}

# Cost metrics (GPU jobs cost more)
jobs_processing_cost_dollars{node_type="standard"}
jobs_processing_cost_dollars{node_type="gpu"}

# P95 latency per job type
jobs_processing_latency_seconds_bucket{job_type="analytics", le="60"}
jobs_processing_latency_seconds_bucket{job_type="ml_inference", le="300"}
```

### Grafana Dashboard

**Jobs Processing Dashboard:**

1. **Queue Health** (gauge)
   - Current queue depth (queued + running)
   - Alert if > 100 jobs backing up

2. **Processing Rate** (graph)
   - Jobs processed per minute
   - Detect if workers are bottleneck

3. **Job Duration Distribution** (histogram)
   - P50, P95, P99 latencies per job type
   - Identify slow job types

4. **Success vs Failure** (pie chart)
   - Percentage of jobs completing successfully
   - Failure rate trend

5. **Cost per Job Type** (bar)
   - GPU jobs vs standard compute cost
   - ROI analysis

---

## 🔄 Example Workflows

### Workflow 1: Analytics Report Generation

```
User Request:
  POST /api/v1/jobs
  {"type": "analytics_report", "params": {"days": 30}}

Timeline:
  T+0s:   Job queued, user gets job ID "job-abc123"
  T+5s:   Worker picks up job, starts processing
  T+45s:  Processing complete, result stored in S3
  T+46s:  User checks status, sees completed with result URL

User:
  curl http://jobs-api/api/v1/jobs/job-abc123
  Response: {"status": "completed", "result_url": "s3://..."}
```

### Workflow 2: ML Inference (GPU)

```
User Request:
  POST /api/v1/jobs
  {"type": "ml_inference", "params": {"model": "billing_fraud_detector", "data": [...]}}

Timeline:
  T+0s:   Job queued (on GPU queue)
  T+10s:  GPU worker acquired, starting inference
  T+120s: Inference complete, results stored
  T+121s: Status returned with predictions

Cost:
  GPU node usage: 2 minutes = $0.033 (10x more expensive than standard)
  Value: Fraud detection prevents $1000+ in losses
  ROI: 30000x
```

---

## 🎯 Failure Handling

### Failure Scenarios

| Scenario | Recovery |
|----------|----------|
| **Job crashes mid-processing** | Retry logic in worker; status -> queued |
| **Worker pod dies** | Kubernetes restarts pod; picks up next job |
| **Database connection drops** | Retry with exponential backoff |
| **Storage unavailable** | Retry storing result; keep result in memory temporarily |
| **Job logic error** | Mark as failed; add to dead-letter queue for review |

### Dead-Letter Queue

```sql
-- Jobs that failed after max retries
CREATE TABLE failed_jobs (
    job_id UUID,
    type VARCHAR(50),
    params JSONB,
    error_message TEXT,
    failed_at TIMESTAMPTZ,
    retry_count INT
);

-- Worker logic:
IF retry_count >= MAX_RETRIES THEN
    INSERT INTO failed_jobs SELECT * FROM jobs WHERE id=job_id
    UPDATE jobs SET status='dead_letter'
    NOTIFY humans: "Job {job_id} failed; needs review"
END IF
```

---

## 🚀 Scaling & Performance

### Horizontal Scaling

```bash
# Monitor queue
watch 'kubectl exec -it postgres -- psql -c "SELECT COUNT(*) FROM jobs WHERE status='\'queued'\'';"'

# Scale workers
kubectl scale deployment jobs-worker --replicas=5 -n team-alpha

# Expected throughput: 1 worker = 1 job/minute (for analytics)
# 5 workers = 5 jobs/minute capacity
```

### Vertical Scaling

**If single job takes too long:**
```yaml
# Before: 1 core, 512Mi
resources:
  requests:
    cpu: 1000m
    memory: 2Gi

# Result: Can run more concurrent logic, faster processing
```

---

## 📈 Future Enhancements

- [ ] **Cron jobs**: Schedule recurring batch jobs
- [ ] **Job dependencies**: "Run job B after job A completes"
- [ ] **Streaming results**: Real-time progress updates for long jobs
- [ ] **Priority queues**: User-settable job priorities
- [ ] **Time limits**: Kill jobs that exceed timeout
- [ ] **Checkpointing**: Resume long jobs from checkpoint on failure
- [ ] **Distributed processing**: Spark-like multi-worker job splits

---

## 📚 Related Documents

- [SRE Playbook](./sre-playbook.md) – Incident response for batch systems
- [FinOps](./finops-notes.md) – Cost tracking for GPU-heavy workloads
- [Architecture Overview](./architecture/README.md) – Batch workload design patterns

---

*Last updated: February 16, 2026*
