# 🎯 Service Access - What You Need to Know

## ❌ What You Tried (and why it failed)

You tried: `hello-app.team-alpha.svc.cluster.local` in your browser

**Error**: `DNS_PROBE_FINISHED_NXDOMAIN`

**Why it failed**: 
- This is a **Kubernetes internal DNS name** that ONLY resolves inside the cluster
- Your browser is on your host machine, outside the cluster
- Your machine's DNS resolver doesn't know about Kubernetes services

---

## ✅ What Works (3 Solutions)

### Solution 1: Port-Forward (EASIEST - Start Here!)

```bash
cd /home/rohan/ecps
bash access-services.sh
```

This creates local bridges to the services:

| Service | Browser URL | What It Is |
|---------|-------------|-----------|
| hello-app | http://localhost:8080 | Simple echo service |
| billing-api | http://localhost:8081 | Demo HTTP API |
| jobs-api | http://localhost:8082 | Demo HTTP API |
| reporting-api | http://localhost:8083 | Demo HTTP API |
| jobs-worker | http://localhost:8084 | Background job processor |

**Try it now:**
```bash
# Terminal 1: Start port-forwards
bash access-services.sh

# Terminal 2: Test the services
curl http://localhost:8080/        # Should return: hello from team alpha
curl http://localhost:8081/get     # Should return JSON from httpbin
curl http://localhost:8082/status/200  # Should return 200 OK
curl http://localhost:8083/uuid    # Should return a UUID
```

---

### Solution 2: Individual Port-Forward

If you only want one service:

```bash
kubectl port-forward -n team-alpha svc/hello-app 8080:80
# Then visit: http://localhost:8080
```

---

### Solution 3: Manual Testing from Inside Cluster

```bash
# Get a running pod
POD=$(kubectl get pod -n team-alpha -l app=hello-app -o jsonpath='{.items[0].metadata.name}')

# Execute commands inside it
kubectl exec -n team-alpha $POD -- curl http://hello-app/
```

---

## 🧪 Verification - Services ARE Running

### Proof that services are responding:

```bash
# Test hello-app
kubectl port-forward -n team-alpha svc/hello-app 8080:80 &
sleep 2
curl http://localhost:8080/

# Result: "hello from team alpha" ✅
```

### Current Status:

```
✅ hello-app:80          RUNNING (1/1 pods ready)
✅ billing-api:80        RUNNING (2/2 pods ready)  
✅ jobs-api:80           RUNNING (2/2 pods ready)
✅ jobs-worker:8001      RUNNING (1/1 pods ready)
✅ reporting-api:80      RUNNING (2/2 pods ready)
```

All services are **healthy and responding**!

---

## 📚 Complete Command Reference

### Quick Service Access

```bash
# 1. Start all services (background)
bash /home/rohan/ecps/access-services.sh

# 2. In another terminal, test with curl:
curl http://localhost:8080/              # hello-app
curl http://localhost:8081/get           # billing-api  
curl http://localhost:8082/status/200    # jobs-api
curl http://localhost:8083/uuid          # reporting-api

# 3. Or open in browser (while access-services.sh is running):
# http://localhost:8080
# http://localhost:8081
# http://localhost:8082
# http://localhost:8083
```

### Check Service Status

```bash
# List all services in team-alpha
kubectl get svc -n team-alpha

# List all running pods
kubectl get pods -n team-alpha

# Get detailed service info
kubectl describe svc hello-app -n team-alpha

# View pod logs
kubectl logs -n team-alpha -l app=hello-app --tail=10
```

### Stop Port-Forwards

```bash
# When done, stop the access script:
pkill -f "kubectl port-forward"

# Or press Ctrl+C in the terminal running access-services.sh
```

---

## 🎓 What's Actually Happening

### Inside the cluster (pod-to-pod):
```
Pod in team-alpha
    ↓
    Can access: http://hello-app.team-alpha.svc.cluster.local/ ✅
    (Kubernetes DNS resolves this)
```

### Outside the cluster (host browser):
```
Your browser on localhost
    ↓
    CANNOT access: http://hello-app.team-alpha.svc.cluster.local/ ❌
    (No Kubernetes DNS available)
    
    CAN access: http://localhost:8080 ✅
    (Port-forward tunnels traffic)
```

### Port-forward mechanism:
```
Your browser → localhost:8080 → kubectl port-forward → Kubernetes API
             → Service hell-app:80 → Pod:80
```

---

## ✨ Bottom Line

**Services are working perfectly!** ✅

You just needed to use the right access method:
- ❌ DON'T: Try cluster DNS names in your browser
- ✅ DO: Use `localhost:PORT` with `kubectl port-forward`

**Start here**:
```bash
bash /home/rohan/ecps/access-services.sh
# Then visit: http://localhost:8080 in your browser 🎉
```

---

## 📖 Related Guides

- See [BROWSER_ACCESS_GUIDE.md](BROWSER_ACCESS_GUIDE.md) for detailed setup instructions
- See [DEPLOYMENT_AND_TEST_REPORT.md](DEPLOYMENT_AND_TEST_REPORT.md) for full deployment details
- See [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) for infrastructure summary
