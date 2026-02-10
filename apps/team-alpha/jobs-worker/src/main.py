import os
import io
import json
import time
from datetime import datetime

import psycopg2
from psycopg2 import errors
import redis
from redis import Redis
from minio import Minio
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# ------------------------------------------------------------
# Environment variables
# ------------------------------------------------------------

PG_HOST = os.getenv("PG_HOST")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
JOB_QUEUE_KEY = os.getenv("JOB_QUEUE_KEY", "jobs:queue")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "jobs-results")

# ------------------------------------------------------------
# Prometheus metrics
# ------------------------------------------------------------

JOBS_PROCESSED_TOTAL = Counter(
    "jobs_worker_jobs_processed_total",
    "Total jobs processed by jobs-worker",
    ["status"],
)

JOB_DURATION_SECONDS = Histogram(
    "jobs_worker_job_duration_seconds",
    "Job processing duration in seconds",
)

REDIS_QUEUE_DEPTH = Gauge(
    "jobs_worker_redis_queue_depth",
    "Current Redis job queue depth",
)

# ------------------------------------------------------------
# Clients
# ------------------------------------------------------------

redis_client: Redis = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)

# ------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------

def get_db_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD,
    )

# ------------------------------------------------------------
# Job processing logic
# ------------------------------------------------------------

def process_cost_report_job(conn, job):
    job_id = job["id"]
    team = job["team"]

    # 1. Aggregate billing data
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(SUM(cost), 0)
                FROM usage_records
                WHERE team = %s
                """,
                (team,),
            )
            total_cost = cur.fetchone()[0]
    except errors.UndefinedTable:
        print("[WARN] usage_records table not found; returning cost=0")
        total_cost = 0

    result = {
        "job_id": job_id,
        "job_type": job["job_type"],
        "team": team,
        "generated_at": datetime.utcnow().isoformat(),
        "total_cost": float(total_cost),
    }

    # 2. Ensure MinIO bucket exists
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)

    # 3. Write result to MinIO (CORRECT FIX)
    object_name = f"{job_id}.json"
    data_bytes = json.dumps(result).encode("utf-8")
    data_stream = io.BytesIO(data_bytes)

    minio_client.put_object(
        MINIO_BUCKET,
        object_name,
        data_stream,
        length=len(data_bytes),
        content_type="application/json",
    )

    result_location = f"s3://{MINIO_BUCKET}/{object_name}"

    # 4. Update job status
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs
            SET status = %s,
                updated_at = %s,
                result_location = %s
            WHERE id = %s
            """,
            ("completed", datetime.utcnow(), result_location, job_id),
        )

# ------------------------------------------------------------
# Main worker loop
# ------------------------------------------------------------

def run_worker():
    print("=== jobs-worker starting up ===")
    print(
        f"PG_HOST={PG_HOST}, PG_DB={PG_DB}, PG_USER={PG_USER}\n"
        f"REDIS_HOST={REDIS_HOST}, REDIS_PORT={REDIS_PORT}\n"
        f"MINIO_ENDPOINT={MINIO_ENDPOINT}, MINIO_BUCKET={MINIO_BUCKET}"
    )
    print("================================")

    conn = get_db_connection()
    conn.autocommit = True

    print("jobs-worker started, polling Redis queue...")

    while True:
        try:
            # Track queue depth
            REDIS_QUEUE_DEPTH.set(redis_client.llen(JOB_QUEUE_KEY))

            # Blocking pop
            _, job_json = redis_client.blpop(JOB_QUEUE_KEY)
            job = json.loads(job_json)

            job_id = job["id"]
            job_type = job["job_type"]
            team = job["team"]

            print(
                f"[jobs-worker] picked job id={job_id} "
                f"type={job_type} team={team}"
            )

            start = time.time()

            if job_type == "cost-report":
                process_cost_report_job(conn, job)
            else:
                raise ValueError(f"Unsupported job_type: {job_type}")

            duration = time.time() - start
            JOB_DURATION_SECONDS.observe(duration)
            JOBS_PROCESSED_TOTAL.labels(status="completed").inc()

            print(f"[jobs-worker] job {job_id} completed in {duration:.3f}s")

        except Exception as e:
            JOBS_PROCESSED_TOTAL.labels(status="failed").inc()
            print(f"[jobs-worker] ERROR processing job: {e}")

            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE jobs
                        SET status = %s,
                            updated_at = %s
                        WHERE id = %s
                        """,
                        ("failed", datetime.utcnow(), job.get("id")),
                    )
            except Exception as db_err:
                print(f"[jobs-worker] ERROR updating job status: {db_err}")

            time.sleep(1)

# ------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------

if __name__ == "__main__":
    # Expose metrics on :8001
    start_http_server(8001)
    run_worker()

