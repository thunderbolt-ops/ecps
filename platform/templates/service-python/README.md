# Python FastAPI Template for ECPS

This is a minimal Python FastAPI service template automatically scaffolded by `ecpsctl service create`.

## Structure

```
service-python/
├── main.py                    # FastAPI application code
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container image definition
├── k8s/
│   ├── deployment.yaml       # Kubernetes Deployment
│   ├── service.yaml          # Kubernetes Service
│   ├── ingress.yaml          # Ingress for HTTP routing
│   └── servicemonitor.yaml   # Prometheus ServiceMonitor
└── tests/
    └── test_main.py          # Unit tests
```

## Development

### Local setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# Service runs on http://localhost:8000
```

### Test locally
```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Building and Deploying

### Build container image
```bash
docker build -t myservice:0.1.0 .
# Or using ecpsctl:
ecpsctl service deploy --name myservice --env dev
```

### Deploy to cluster
```bash
kubectl apply -f k8s/
# Or using ecpsctl:
ecpsctl service deploy --name myservice --env dev
```

## Monitoring

- **Health endpoint:** `/health` (liveness probe)
- **Readiness endpoint:** `/ready` (readiness probe)
- **Metrics endpoint:** `/metrics` (Prometheus scraping)

## Key Libraries

- **FastAPI:** Modern web API framework
- **Prometheus client:** Metrics instrumentation
- **Pydantic:** Request/response validation
- **uvicorn:** ASGI server

## Next Steps

1. Add your business logic endpoints to `main.py`
2. Add dependencies to `requirements.txt`
3. Add unit tests to `tests/`
4. Update the `SERVICE_NAME` in deployment config
5. Deploy using: `ecpsctl service deploy --name myservice`

## Documentation

- Full template: [Python Service Guide](../../docs/ai-batch-architecture.md#python-implementation)
- Platform guide: [README.md](../../README.md)
