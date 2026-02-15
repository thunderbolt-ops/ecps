# 🌐 How to Access ECPS Services in Your Browser

## The Problem You Encountered

You tried to visit `hello-app.team-alpha.svc.cluster.local` in your browser and got:
```
This site can't be reached
Check if there is a typo in hello-app.team-alpha.svc.cluster.local.
DNS_PROBE_FINISHED_NXDOMAIN
```

**This is expected!** Here's why:

### DNS Resolution Context
- **Inside the Kubernetes cluster** (inside pods): Services are discoverable by their DNS name
  - Example: `http://hello-app.team-alpha.svc.cluster.local/` ✅ Works
  - This works because pods use the cluster's DNS server (CoreDNS)

- **Outside the Kubernetes cluster** (your host browser): Cluster DNS names are NOT resolvable
  - Example: `http://hello-app.team-alpha.svc.cluster.local/` ❌ Fails (DNS_PROBE_FINISHED_NXDOMAIN)
  - Your browser uses your machine's DNS, which knows nothing about Kubernetes internal names

---

## ✅ Solution 1: Use Port-Forwarding (Easiest)

Port-forwarding creates a local tunnel from your browser to the cluster service.

### Quick Start

```bash
cd /home/rohan/ecps && bash access-services.sh
```

This script automatically:
- ✅ Kills any existing port-forwards
- ✅ Creates tunnels for all 5 services
- ✅ Displays ready-to-use localhost URLs
- ✅ Shows example endpoints to try

### Manual Port-Forward Commands

If you prefer manual control:

```bash
# Hello App - Simple echo service
kubectl port-forward -n team-alpha svc/hello-app 8080:80

# In another terminal:
# Then visit: http://localhost:8080
```

Open multiple terminals for multiple services:

```bash
# Terminal 1
kubectl port-forward -n team-alpha svc/hello-app 8080:80

# Terminal 2
kubectl port-forward -n team-alpha svc/billing-api 8081:80

# Terminal 3
kubectl port-forward -n team-alpha svc/jobs-api 8082:80

# Terminal 4
kubectl port-forward -n team-alpha svc/reporting-api 8083:80
```

### Accessing Services (One Connected)

| Service | Local URL | Example |
|---------|-----------|---------|
| hello-app | http://localhost:8080 | http://localhost:8080/ |
| billing-api | http://localhost:8081 | http://localhost:8081/get |
| jobs-api | http://localhost:8082 | http://localhost:8082/status/200 |
| reporting-api | http://localhost:8083 | http://localhost:8083/uuid |
| jobs-worker | http://localhost:8084 | http://localhost:8084/ |

---

## ✅ Solution 2: Use Ingress (For Real Domains)

For permanent, production-like access, use Kubernetes Ingress:

### Step 1: Set up local domain mapping

Add to your `/etc/hosts` file:
```
127.0.0.1  hello-app.local
127.0.0.1  billing-api.local
127.0.0.1  jobs-api.local
127.0.0.1  reporting-api.local
```

### Step 2: Create Ingress resources

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: team-alpha-ingress
  namespace: team-alpha
spec:
  ingressClassName: nginx
  rules:
    - host: hello-app.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: hello-app
                port:
                  number: 80
    - host: billing-api.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: billing-api
                port:
                  number: 80
```

### Step 3: Port-forward ingress

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 80:80
```

### Step 4: Access via browser

- http://hello-app.local
- http://billing-api.local
- http://jobs-api.local
- http://reporting-api.local

---

## ✅ Solution 3: Use kubectl exec (For Testing)

Test services from inside the cluster:

```bash
# Get a pod from hello-app
POD=$(kubectl get pod -n team-alpha -l app=hello-app -o jsonpath='{.items[0].metadata.name}')

# Execute a command inside it (it's a busybox, limited tools)
kubectl exec -n team-alpha $POD -- sh -c 'echo "Testing from inside cluster..."'
```

---

## 📝 Quick Reference

### To check what services are running:
```bash
kubectl get svc -n team-alpha
```

### To check what pods are running:
```bash
kubectl get pods -n team-alpha
```

### To view pod logs:
```bash
kubectl logs -n team-alpha -l app=billing-api --tail=50
```

### To describe a service:
```bash
kubectl describe svc hello-app -n team-alpha
```

### To test with curl (after port-forward):
```bash
curl http://localhost:8080/
curl http://localhost:8081/get
curl http://localhost:8082/headers
curl http://localhost:8083/uuid
```

---

## 🎯 Recommended Workflow

1. **For quick testing**: Use `bash access-services.sh` to start all port-forwards
2. **For browser access**: Visit http://localhost:8080 etc. while script is running
3. **For API testing**: Use curl with the localhost endpoints
4. **For production**: Set up Ingress for domain-based access

---

## Troubleshooting

### Port already in use?
```bash
# Kill existing port-forwards
pkill -f "kubectl port-forward"

# Or find what's using the port
lsof -i :8080
```

### Port-forward disconnected?
```bash
# Re-run the script
bash access-services.sh
```

### Service not responding?
```bash
# Check if service exists
kubectl get svc hello-app -n team-alpha

# Check if pods are running
kubectl get pods -n team-alpha -l app=hello-app

# Check pod logs
kubectl logs -n team-alpha $(kubectl get pod -n team-alpha -l app=hello-app -o jsonpath='{.items[0].metadata.name}')
```

### Still getting DNS error?
- Make sure you're using `localhost` or `127.0.0.1`, not the cluster domain
- Do NOT try to access `hello-app.team-alpha.svc.cluster.local` from your browser
- That URL only works from inside the cluster (inside pods)

---

## Summary

| Access Method | URL | How | When to Use |
|---------------|-----|-----|------------|
| **Port-Forward** | `localhost:PORT` | `kubectl port-forward` | ✅ Quick testing, development |
| **Ingress** | `service.local` | Set up Ingress + /etc/hosts | ✅ Production-like, realistic |
| **kubectl exec** | N/A | `kubectl exec pod -- curl` | ✅ Testing from inside cluster |

**Start here**: `bash access-services.sh` then visit http://localhost:8080 🎉
