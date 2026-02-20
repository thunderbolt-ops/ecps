# 🚀 ECPS Quick Start Guide

## Your Platform is Ready! Here's How to Use It

### ⚡ 30-Second Start

```bash
cd /home/rohan/ecps
bash access-services.sh
# Open browser to http://localhost:8080
```

---

## 📍 What's Running

| Service | Status | URL | Command |
|---------|--------|-----|---------|
| **hello-app** | ✅ 1/1 | http://localhost:8080 | `curl localhost:8080/` |
| **billing-api** | ✅ 2/2 | http://localhost:8081 | `curl localhost:8081/get` |
| **jobs-api** | ✅ 2/2 | http://localhost:8082 | `curl localhost:8082/status/200` |
| **reporting-api** | ✅ 2/2 | http://localhost:8083 | `curl localhost:8083/uuid` |
| **jobs-worker** | ✅ 1/1 | http://localhost:8084 | Status endpoint |

---

## 🎯 Access Methods (Ranked by Ease)

### Method 1: Auto Port-Forwards ⭐⭐⭐ (Easiest)
```bash
bash /home/rohan/ecps/access-services.sh
# All 5 services now at localhost:8080-8084
```

### Method 2: Manual Port-Forward
```bash
kubectl port-forward -n team-alpha svc/hello-app 8080:80
# Then visit http://localhost:8080
# Keep terminal open or add & to background
```

### Method 3: Terminal Testing (No Browser)
```bash
# Start one port-forward in background
kubectl port-forward -n team-alpha svc/hello-app 8080:80 &

# Test from command line
curl http://localhost:8080/
curl http://localhost:8081/get

# Stop all
pkill -f "kubectl port-forward"
```

### Method 4: Cluster-Internal Testing
```bash
# This works inside the cluster (pods have access to CoreDNS)
kubectl exec -it -n team-alpha hello-app-XXXX -c hello-app -- sh
curl http://hello-app.team-alpha.svc.cluster.local/
```

---

## ✅ Verification Checklist

- [ ] Run `bash access-services.sh` → should see "✅ Port-forwards active!"
- [ ] Visit http://localhost:8080 in browser → should see "hello from team alpha"
- [ ] Run `curl http://localhost:8080/` → should get response
- [ ] Run `kubectl get pods -n team-alpha` → should see 8 pods as "Running"
- [ ] Run `kubectl get svc -n team-alpha` → should see 5 services with IPs

---

## 🔧 Useful Commands

```bash
# View all services
kubectl get svc -n team-alpha

# View all pods
kubectl get pods -n team-alpha

# View pod logs (last 50 lines)
kubectl logs -n team-alpha pod/hello-app-XXXX --tail=50

# Describe a service (shows endpoints)
kubectl describe svc hello-app -n team-alpha

# Execute command in a pod
kubectl exec -n team-alpha pod/hello-app-XXXX -- curl http://localhost/

# Stop all port-forwards
pkill -f "kubectl port-forward"

# Check node status
kubectl get nodes

# View all namespaces
kubectl get namespaces
```

---

## 📚 Understanding the DNS Error You Got

### ❌ What DIDN'T Work
```
http://hello-app.team-alpha.svc.cluster.local  ← Cluster internal DNS
# Browser says: DNS_PROBE_FINISHED_NXDOMAIN
# Why: Your browser is OUTSIDE the cluster, can't use cluster DNS
```

### ✅ What DOES Work
```
http://localhost:8080/  ← Port-forward creates a LOCAL bridge
# Works perfectly because localhost is on your machine
```

---

## 🏗️ Infrastructure Summary

- **Kubernetes Cluster**: Kind (Kubernetes in Docker) running v1.28.1
- **Cluster Name**: ecps-stage
- **Active Namespaces**: 6 (platform-system, platform-data, platform-identity, platform-observability, team-alpha, team-beta)
- **Running Pods**: 8 in team-alpha + 15+ in platform namespaces
- **Services**: 5 deployed in team-alpha namespace
- **Infrastructure as Code**: 42 Terraform resources deployed
- **Status**: ✅ FULLY OPERATIONAL

---

## 📖 Detailed Guides

For more detailed information, see:

- **SERVICE_ACCESS_EXPLAINED.md** - Why DNS failed and how the fix works
- **BROWSER_ACCESS_GUIDE.md** - Complete guide with all access methods and troubleshooting (300+ lines)
- **DEPLOYMENT_AND_TEST_REPORT.md** - Full deployment summary with test results

---

## 🚀 Next Steps

1. **Try it now**: `bash access-services.sh`
2. **Visit in browser**: http://localhost:8080
3. **Run curl tests**: 
   ```bash
   curl http://localhost:8080/
   curl http://localhost:8081/get
   ```
4. **Check logs**: `kubectl logs -n team-alpha -l app=hello-app`
5. **Stop when done**: `pkill -f "kubectl port-forward"`

---

## ❓ Common Questions

**Q: Why can't I use the DNS name from my browser?**  
A: Kubernetes DNS names are only available inside the cluster. Port-forward creates a local bridge (localhost:PORT) that works from your machine.

**Q: Will the port-forwards stay running?**  
A: Only while the script is running. Keep the terminal window open, or use `&` to run in background.

**Q: Can I change the port numbers?**  
A: Yes! Edit `access-services.sh` and change the numbers before the colons (8080, 8081, etc.)

**Q: How do I stop everything?**  
A: `pkill -f "kubectl port-forward"` kills all port-forwards.

**Q: Why are there 2 pods per service?**  
A: The demo deployments are configured with 2 replicas for high availability testing.

---

## 📞 Troubleshooting

**Port already in use?**
```bash
# Find what's using the port
lsof -i :8080
# Kill it if needed
kill -9 <PID>
```

**Port-forward won't start?**
```bash
# Make sure kubectl can talk to the cluster
kubectl get nodes
# Make sure services exist
kubectl get svc -n team-alpha
```

**Services not responding?**
```bash
# Check if pods are running
kubectl get pods -n team-alpha
# Check logs
kubectl logs -n team-alpha -l app=hello-app
```

---

**Status**: ✅ All systems operational and ready to use!

**Time spent**: Infrastructure setup, deployment, testing, and documentation complete

**Next action**: Run `bash access-services.sh` and enjoy your platform!

