#!/bin/bash
# ECPS Service Port-Forward Setup Script
# This script creates local browser-accessible endpoints for all team-alpha services
# Run: bash access-services.sh

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ECPS - Service Port-Forward Setup                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Setting up kubectl port-forwards to access services locally..."
echo ""

# Kill any existing port-forwards
pkill -f "kubectl port-forward" || true
sleep 1

# Start port-forwards in background
kubectl port-forward -n team-alpha svc/hello-app 8080:80 > /tmp/pf-hello-app.log 2>&1 &
PF_HELLO=$!
echo "✅ hello-app:80 → localhost:8080"

kubectl port-forward -n team-alpha svc/billing-api 8081:80 > /tmp/pf-billing-api.log 2>&1 &
PF_BILLING=$!
echo "✅ billing-api:80 → localhost:8081"

kubectl port-forward -n team-alpha svc/jobs-api 8082:80 > /tmp/pf-jobs-api.log 2>&1 &
PF_JOBS=$!
echo "✅ jobs-api:80 → localhost:8082"

kubectl port-forward -n team-alpha svc/jobs-worker 8084:8001 > /tmp/pf-jobs-worker.log 2>&1 &
PF_WORKER=$!
echo "✅ jobs-worker:8001 → localhost:8084"

kubectl port-forward -n team-alpha svc/reporting-api 8083:80 > /tmp/pf-reporting-api.log 2>&1 &
PF_REPORTING=$!
echo "✅ reporting-api:80 → localhost:8083"

# Wait for port-forwards to be ready
sleep 2

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🌐 SERVICES NOW ACCESSIBLE IN YOUR BROWSER         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 HELLO-APP (Simple echo service)"
echo "   Browser: http://localhost:8080"
echo "   Response: 'hello from team alpha'"
echo ""
echo "💰 BILLING-API (HTTPBin demo)"
echo "   Browser: http://localhost:8081"
echo "   Try: http://localhost:8081/get"
echo "   Try: http://localhost:8081/uuid"
echo ""
echo "📋 JOBS-API (HTTPBin demo)"
echo "   Browser: http://localhost:8082"
echo "   Try: http://localhost:8082/status/200"
echo "   Try: http://localhost:8082/headers"
echo ""
echo "📊 REPORTING-API (HTTPBin demo)"
echo "   Browser: http://localhost:8083"
echo "   Try: http://localhost:8083/delay/1"
echo "   Try: http://localhost:8083/base64"
echo ""
echo "⚙️  JOBS-WORKER (Background job processor)"
echo "   Health: http://localhost:8084"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "Port-forward background processes running. Stop with:"
echo "  pkill -f 'kubectl port-forward'"
echo ""
echo "Or press Ctrl+C to terminate this script."
echo ""

# Keep script running until interrupted
trap "echo ''; echo 'Stopping port-forwards...'; pkill -f 'kubectl port-forward' || true; exit 0" EXIT

# Wait indefinitely
wait
