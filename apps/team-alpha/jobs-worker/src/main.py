import os
import io
import json
import time
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2 import errors, pool
import redis
from redis import Redis
from minio import Minio
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configure structured logging
class StructuredLogger:
    """JSON structured logging with context."""
    def __init__(self, service_name, team, environment):
        self.service_name = service_name
        self.team = team
        self.environment = environment
        self.logger = logging.getLogger(service_name)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log(self, level, message, **context):
        log_context = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "team": self.team,
            "environment": self.environment,
            "level": level,
            "message": message,
        }
        log_context.update(context)
        self.logger.info(json.dumps(log_context))

APP_TEAM = os.getenv("APP_TEAM", "team-alpha")
APP_ENV = os.getenv("APP_ENV", "dev")
logger = StructuredLogger("jobs-worker", APP_TEAM, APP_ENV)

# ========================================================================
# Environment variables
# ========================================================================

PG_HOST = os.getenv("PG_HOST", "postgres.platform-data.svc.cluster.local")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "billing")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dev-postgres-password")

REDIS_HOST = os.getenv("REDIS_HOST", "redis.platform-data.svc.cluster.local")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
JOB_QUEUE_KEY = os.getenv("JOB_QUEUE_KEY", "jobs:queue")
DEADLETTER_QUEUE_KEY = "jobs:deadletter"

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio.platform-data.svc.cluster.local:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "jobs-results")

# Retry configuration
MAX_RETRIES = int(os.getenv("JOB_MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("JOB_RETRY_DELAY", "5"))
POLL_INTERVAL_SECONDS = int(os.getenv("JOB_POLL_INTERVAL", "2"))

# ========================================================================
# Prometheus metrics
# ========================================================================

JOBS_PROCESSED_TOTAL = Counter(
    "jobs_worker_jobs_processed_total",
    "Total jobs processed by jobs-worker",
    ["status", "job_type"],
)

JOB_DURATION_SECONDS = Histogram(
    "jobs_worker_job_duration_seconds",
    "Job processing duration in seconds",
    ["job_type"],
)

JOB_RETRY_TOTAL = Counter(
    "jobs_worker_job_retries_total",
    "Total job retries",
    ["job_type"],
)

JOB_DEADLETTER_TOTAL = Counter(
    "jobs_worker_job_deadletter_total",
    "Jobs sent to deadletter queue",
    ["job_type"],
)

REDIS_QUEUE_DEPTH = Gauge(
    "jobs_worker_redis_queue_depth",
    "Current Redis job queue depth",
)

DEADLETTER_QUEUE_DEPTH = Gauge(
    "jobs_worker_deadletter_queue_depth",
    "Current deadletter queue depth",
)

# Job cost tracking
JOB_COST_PROCESSED = Counter(
    "jobs_worker_job_cost_processed_total",
    "Total cost of processed jobs (USD)",
    ["job_type", "status"],
)

JOB_COST_BY_TYPE = {
    "analytics_report": 0.50,
    "ml_inference": 5.00,
    "data_simulation": 1.00,
}

# ========================================================================
# Clients with connection pooling
# ========================================================================

pg_connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=PG_HOST,
    port=PG_PORT,
    dbname=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD,
)

redis_client: Redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
)

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# ========================================================================
# Job processing logic
# ========================================================================

def process_analytics_report_job(conn, job: dict) -> dict:
    """Process analytics/cost report job."""
    job_id = job["id"]
    team = job["team"]
    params = job.get("parameters", {})

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(cost), 0), COUNT(*) as record_count
                FROM usage_records
                WHERE team = %s
                """,
                (team,),
            )
            total_cost, record_count = cur.fetchone()

        result = {
            "job_id": job_id,
            "job_type": job["job_type"],
            "team": team,
            "generated_at": datetime.utcnow().isoformat(),
            "total_cost": float(total_cost),
            "record_count": record_count,
        }
        
        logger.log("info", "Analytics report generated", job_id=job_id, 
                  team=team, total_cost=total_cost, record_count=record_count)
        
        return result
    except Exception as e:
        logger.log("error", "Failed to generate analytics report", 
                  job_id=job_id, error=str(e))
        raise


def process_ml_inference_job(conn, job: dict) -> dict:
    """Process ML inference job (GPU workload)."""
    job_id = job["id"]
    team = job["team"]
    
    # Simulate GPU inference processing
    time.sleep(2)
    
    result = {
        "job_id": job_id,
        "job_type": job["job_type"],
        "team": team,
        "generated_at": datetime.utcnow().isoformat(),
        "inference_result": "ML model prediction complete",
        "gpu_time_seconds": 2.0,
    }
    
    logger.log("info", "ML inference completed", job_id=job_id, team=team, gpu_time=2.0)
    return result


def process_data_simulation_job(conn, job: dict) -> dict:
    """Process data simulation job."""
    job_id = job["id"]
    team = job["team"]
    
    # Simulate data generation
    time.sleep(1)
    
    result = {
        "job_id": job_id,
        "job_type": job["job_type"],
        "team": team,
        "generated_at": datetime.utcnow().isoformat(),
        "records_generated": 1000,
    }
    
    logger.log("info", "Data simulation completed", job_id=job_id, team=team, records=1000)
    return result


JOB_PROCESSORS = {
    "analytics_report": process_analytics_report_job,
    "cost-report": process_analytics_report_job,  # Backward compatibility
    "ml_inference": process_ml_inference_job,
    "data_simulation": process_data_simulation_job,
}


def update_job_status(conn, job_id: str, status: str, result_location: Optional[str] = None, error: Optional[str] = None):
    """Update job status in database."""
    try:
        with conn.cursor() as cur:
            if error:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = %s,
                        updated_at = %s,
                        result_location = %s,
                        parameters = jsonb_set(
                            COALESCE(parameters, '{}'::jsonb),
                            '{error}',
                            %s
                        )
                    WHERE id = %s
                    """,
                    (status, datetime.utcnow(), result_location, json.dumps(error), job_id),
                )
            else:
                cur.execute(
                    """
                    UPDATE jobs
                    SET status = %s,
                        updated_at = %s,
                        result_location = %s
                    WHERE id = %s
                    """,
                    (status, datetime.utcnow(), result_location, job_id),
                )
        conn.commit()
    except Exception as e:
        logger.log("error", "Failed to update job status", job_id=job_id, status=status, error=str(e))
        raise


def process_job(job: dict) -> bool:
    """
    Process a single job.
    Returns True if successful, False if should retry.
    Raises exception if should go to deadletter queue.
    """
    job_id = job["id"]
    job_type = job.get("job_type", "unknown")
    team = job.get("team", "unknown")
    
    try:
        # Get database connection
        conn = pg_connection_pool.getconn()
        conn.autocommit = True
        
        start_time = time.time()
        
        # Get processor function
        processor = JOB_PROCESSORS.get(job_type)
        if not processor:
            raise ValueError(f"Unsupported job_type: {job_type}")
        
        # Process the job
        result = processor(conn, job)
        
        # Store result to MinIO
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
        
        object_name = f"results/{job_id}.json"
        result_bytes = json.dumps(result).encode("utf-8")
        result_stream = io.BytesIO(result_bytes)
        
        minio_client.put_object(
            MINIO_BUCKET,
            object_name,
            result_stream,
            length=len(result_bytes),
            content_type="application/json",
        )
        
        result_location = f"s3://{MINIO_BUCKET}/{object_name}"
        
        # Update job status to completed
        update_job_status(conn, job_id, "completed", result_location=result_location)
        
        duration = time.time() - start_time
        JOB_DURATION_SECONDS.labels(job_type=job_type).observe(duration)
        JOBS_PROCESSED_TOTAL.labels(status="completed", job_type=job_type).inc()
        
        job_cost = JOB_COST_BY_TYPE.get(job_type, 0.50)
        JOB_COST_PROCESSED.labels(job_type=job_type, status="completed").inc(job_cost)
        
        logger.log("info", "Job processed successfully", job_id=job_id, job_type=job_type,
                  team=team, duration=duration, cost=job_cost)
        
        pg_connection_pool.putconn(conn)
        return True
        
    except Exception as e:
        error_msg = str(e)
        logger.log("error", "Job processing failed", job_id=job_id, job_type=job_type,
                  team=team, error=error_msg)
        
        JOBS_PROCESSED_TOTAL.labels(status="failed", job_type=job_type).inc()
        
        try:
            pg_connection_pool.putconn(conn)
        except:
            pass
        
        raise


def push_to_deadletter(job: dict):
    """Move job to deadletter queue when retries exhausted."""
    redis_client.rpush(DEADLETTER_QUEUE_KEY, json.dumps(job))
    
    job_type = job.get("job_type", "unknown")
    JOB_DEADLETTER_TOTAL.labels(job_type=job_type).inc()
    
    logger.log("warning", "Job moved to deadletter queue", 
              job_id=job["id"], job_type=job_type, team=job.get("team"))


def should_retry(job: dict) -> bool:
    """Check if a job should be retried."""
    retry_count = job.get("retry_count", 0)
    return retry_count < MAX_RETRIES


# ========================================================================
# Graceful shutdown
# ========================================================================

should_exit = False

def signal_handler(signum, frame):
    global should_exit
    logger.log("info", "Received shutdown signal")
    should_exit = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ========================================================================
# Main worker loop
# ========================================================================

def run_worker():
    logger.log("info", "jobs-worker starting up")
    logger.log("info", "Configuration", pg_host=PG_HOST, pg_db=PG_DB,
              redis_host=REDIS_HOST, redis_port=REDIS_PORT,
              minio_endpoint=MINIO_ENDPOINT, minio_bucket=MINIO_BUCKET,
              max_retries=MAX_RETRIES)
    
    logger.log("info", "jobs-worker started, polling Redis queue")
    
    global should_exit

    while not should_exit:
        try:
            # Update queue depth metrics
            REDIS_QUEUE_DEPTH.set(redis_client.llen(JOB_QUEUE_KEY))
            DEADLETTER_QUEUE_DEPTH.set(redis_client.llen(DEADLETTER_QUEUE_KEY))

            # Blocking pop with timeout to allow graceful shutdown
            result = redis_client.blpop(JOB_QUEUE_KEY, timeout=POLL_INTERVAL_SECONDS)
            
            if not result:
                continue
            
            _, job_json = result
            job = json.loads(job_json)
            job_id = job.get("id")
            
            try:
                # Try to process the job
                process_job(job)
                
            except Exception as e:
                # Check if we should retry
                job["retry_count"] = job.get("retry_count", 0) + 1
                
                if should_retry(job):
                    # Push back to queue for retry
                    JOB_RETRY_TOTAL.labels(job_type=job.get("job_type")).inc()
                    redis_client.rpush(JOB_QUEUE_KEY, json.dumps(job))
                    logger.log("warning", "Job queued for retry", job_id=job_id,
                              retry_count=job["retry_count"], max_retries=MAX_RETRIES)
                else:
                    # Move to deadletter queue
                    push_to_deadletter(job)

        except KeyboardInterrupt:
            logger.log("info", "Keyboard interrupt received")
            should_exit = True
            break
        except Exception as e:
            logger.log("error", "Unexpected error in worker loop", error=str(e))
            time.sleep(1)

    logger.log("info", "jobs-worker shutting down gracefully")


# ========================================================================
# Entrypoint
# ========================================================================

if __name__ == "__main__":
    try:
        # Expose metrics on :8001
        start_http_server(8001)
        run_worker()
    except Exception as e:
        logger.log("error", "Worker crashed", error=str(e))
        sys.exit(1)
    finally:
        if pg_connection_pool:
            pg_connection_pool.closeall()
        logger.log("info", "Worker shutdown complete")

