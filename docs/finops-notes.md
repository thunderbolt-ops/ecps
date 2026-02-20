# FinOps & Cost Management

**How ECPS tracks, understands, and optimizes cloud costs.**

This document covers:
- Cost model and measurement
- Per-team cost attribution
- Capacity planning and optimization
- Cost alerts and dashboards
- Chargeback and accountability

---

## 💰 Cost Model

### Virtual Pricing Model

ECPS uses a **simplified virtual cost model** to simulate cloud pricing:

| Resource Type | Virtual Cost | Notes |
|---------------|--------------|-------|
| **CPU (per core-hour)** | $0.10 | Based on AWS t3 instances |
| **Memory (per GB-hour)** | $0.02 | Based on AWS pricing |
| **Storage (per GB/month)** | $0.01 | Postgres, persistent volumes |
| **GPU Node (per core-hour)** | $1.00 | 10x premium for "GPU" nodes |
| **Data Transfer (per GB)** | $0.01 | Egress traffic simulation |

### Example Cost Calculations

#### Service: billing-api (2 replicas)
```
CPU Request:    2 cores × 2 replicas = 4 core-hours/day
Memory Request: 256Mi × 2 replicas × 24h = 12 GB-hours/day

Daily Compute Cost:
  = (4 cores × $0.10) + (12 GB × $0.02)
  = $0.40 + $0.24
  = $0.64 per day
  = ~$19/month
```

#### Service: gpu-batch-worker (on GPU node) (1 replica)
```
CPU Request:    2 cores × 1 replica = 2 core-hours/day (on GPU node)
GPU Premium:    2 cores × $1.00 = $2.00 per day

Daily GPU Cost:
  = (2 cores × $1.00)
  = $2.00 per day
  = ~$60/month (10x higher than standard compute)
```

---

## 📊 Cost Attribution Model

### Dimensions

Cost is tracked across three primary dimensions:

```
Cost = Team × Service × Environment × Time
```

#### 1. **Team Dimension**
- `team-alpha`
- `team-beta`
- `platform` (shared infrastructure)

#### 2. **Service Dimension**
Per-team services:
- `billing-api` (team-alpha)
- `reporting-api` (team-alpha)
- `jobs-api` (team-alpha)
- `jobs-worker` (team-alpha)
- `hello-app` (team-alpha)

Shared services:
- `postgres` (platform)
- `redis` (platform)
- `minio` (platform)
- `keycloak` (platform)
- `argocd` (platform)

#### 3. **Environment Dimension**
- `dev` (lower cost, 1x replicas)
- `stage` (medium cost, 2x replicas)
- `prod` (higher cost, 3x replicas + reserved capacity)

#### 4. **Time Dimension**
- Hourly cost tracking
- Daily aggregation
- Monthly billing periods
- Year-to-date summaries

### Cost Allocation Strategy

**Team Services** (Direct Cost):
- 100% of cost attributed to owning team
- Example: billing-api cost → team-alpha

**Shared Services** (Distributed Cost):
- PostgreSQL: Cost distributed to all teams using it (weighted by table size)
- Redis: Cost distributed to teams using the cache (weighted by connections)
- ArgoCD: Cost distributed uniformly across teams
- Platform: Shared platform cost distributed uniformly to all teams

**Formula:**
```
Team Monthly Cost = Σ(Direct Service Costs) + (Share of Platform Costs)

Example for team-alpha:
  = cost(billing-api) + cost(reporting-api) + cost(jobs-api) + cost(jobs-worker) + cost(hello-app)
    + (team-alpha's share of postgres cost)
    + (team-alpha's share of redis cost)
    + (1/2 × platform cost, shared with team-beta)
```

---

## 📈 Monitoring & Reporting

### Cost Metrics in Prometheus

All services expose cost-related metrics:

```prometheus
# Service-level resource costs (updated periodically)
ecps_service_cost_cpu_dollars{team="team-alpha", service="billing-api", env="dev"}
ecps_service_cost_memory_dollars{team="team-alpha", service="billing-api", env="dev"}
ecps_service_cost_total_per_hour{team="team-alpha", service="billing-api", env="dev"}

# Platform-level aggregations
ecps_team_cost_total{team="team-alpha", env="dev", period="monthly"}
ecps_environment_cost_total{env="dev", period="monthly"}

# Cost per workload characteristic
ecps_cost_gpu_vs_standard{node_type="gpu"}
```

### Cost Dashboard (Grafana)

**Title**: ECPS Cost Breakdown

**Panels:**

1. **Top 10 Most Expensive Services** (pie chart)
   - Shows which services consume the most budget
   - Click to drill into service details

2. **Cost by Team** (bar chart)
   - Monthly cost for team-alpha vs team-beta vs platform
   - Trends over last 3 months

3. **Cost by Environment** (stacked area)
   - Dev vs Stage vs Prod cost trend
   - Identify cost reduction opportunities

4. **Cost per Request** (line chart)
   - billing-api: cost per invoice generated
   - reporting-api: cost per report generated
   - jobs-worker: cost per job processed
   - **Purpose**: Understand business value vs cost

5. **GPU vs Standard Compute** (horizontal bar)
   - GPU workloads and their premium cost
   - Identify candidates for optimization

6. **Resource Utilization vs Requested** (table)
   - Actual CPU/Memory used vs requested
   - **Waste indicator**: High gap = over-provisioned

---

## 🎯 Cost Optimization Strategies

### Strategy 1: Right-Sizing (Highest ROI)

**Goal**: Allocate true amount of CPU/memory needed, eliminate waste

**Metrics to monitor:**
- CPU Utilization: `actual_cpu / requested_cpu`
- Memory Utilization: `actual_memory / requested_memory`

**Targets:**
- Target utilization: 70-80%
- Anything <20%: Candidate for down-sizing
- Anything >90%: Candidate for up-sizing

**Example:**
```
Current: billing-api requests 500m CPU, uses ~100m
  = 100/500 = 20% utilization (WASTE)

Action: Reduce request to 200m
  = 100/200 = 50% utilization (GOOD)
  = $0.04/day → $0.02/day (50% savings)

Monthly Savings: $0.60 per replica × 2 replicas = $1.20/month
```

### Strategy 2: Replica Optimization

**Goal**: Run only as many replicas as needed for reliability

**Trade-off:**
- More replicas = higher availability, higher cost
- Fewer replicas = lower cost, lower availability
- Goal: SLO-driven replica counts, not over-provisioned

**Decision Framework:**
```
If   error_budget > 30% → Can reduce replicas
If   error_budget < 10% → May need more replicas
If   p99_latency < SLO   → Could reduce replicas if still SLO-compliant
```

**Example:**
```
Current: billing-api = 2 replicas (dev environment)
  = Cost: $19/month

Action: Reduce to 1 replica (dev has lower SLO targets)
  = Cost: $9.50/month
  = Savings: $9.50/month (50%)

Risk: Lower availability, but acceptable in dev

Monitor: If error budget starts to burn faster, revert to 2
```

### Strategy 3: Environment-Specific Tuning

**Goal**: Match environment resources to actual requirements

| Consideration | Dev | Stage | Prod |
|---------------|-----|-------|------|
| **Replicas** | 1 | 2 | 3 |
| **CPU Request** | 100m | 200m | 250m |
| **Memory Request** | 128Mi | 256Mi | 512Mi |
| **Storage Retention** | 7d | 30d | 90d |
| **Expected Cost** | $5 | $15 | $50 |

**Action**: Don't carry prod-sized resources in dev

### Strategy 4: Batch Job Optimization

**Goal**: Schedule expensive jobs efficiently

**Current (Inefficient):**
```
GPU job: 1 GPU core-hour = $1.00
Running 100 jobs/day, each 1 hour = $100/day
```

**Optimized:**
```
Batch job: Queue 100 jobs, process in parallel on 4-core GPU
Time: 25 hours total (4 jobs in parallel)
Cost: 25 GPU core-hours = $25/day

Savings: $75/day = $2,250/month
```

### Strategy 5: Shared Service Consolidation

**Goal**: Pool shared services instead of per-team duplication

**Anti-pattern:**
```
team-alpha: Postgres (512Mi) = $10/month
team-beta:  Postgres (512Mi) = $10/month
Total: $20/month
```

**Better:**
```
Shared:     Postgres (1Gi) with namespaced schemas = $15/month
team-alpha: Uses shared Postgres (pay share: $7.50)
team-beta:  Uses shared Postgres (pay share: $7.50)
Total: $15/month ($5 savings)
```

---

## 💡 Cost Alerts

### Alert: Cost Spike Detection

```prometheus
alert: CostSpikeTooHigh
  expr: rate(ecps_team_cost_total[1h]) > 1.2 * avg_over_time(ecps_team_cost_total[7d])
  for: 5m
  annotations:
    summary: "Cost spike for {{ $labels.team }}"
    description: "Hourly cost is 20% higher than 7-day average"
```

**Action**: Investigate new deployments, check for resource spills

### Alert: Budget Overage

```prometheus
alert: TeambBudgetOverage
  expr: ecps_team_cost_total{period="monthly"} > 150
  for: 0m
  annotations:
    summary: "team-alpha exceeded monthly budget of $150"
```

**Action**: Review cost dashboard, plan optimizations for next month

### Alert: Inefficient Resource Request

```prometheus
alert: WastefulResourceRequest
  expr: (rate(container_cpu_usage_seconds_total) / container_spec_cpu_quota) < 0.2
  for: 1h
  annotations:
    summary: "Pod {{ $labels.pod }} using <20% of CPU request"
```

**Action**: Right-size resource requests

---

## 📊 Cost Reports & Chargeback

### Monthly Cost Report Template

```
ECPS Monthly Cost Report – February 2026

EXECUTIVE SUMMARY
────────────────
Total Platform Cost:        $256
  Dev Environment:          $45
  Stage Environment:        $75
  Prod Environment:         $136

Team Allocation:
  team-alpha:               $150 (58%)
  team-beta:                $75 (29%)
  Platform (shared):        $31 (13%)

DETAILED BREAKDOWN
────────────────

Team Alpha
  billing-api (dev):        $19     3.5 requests/sec avg
  billing-api (stage):      $38     0.8 requests/sec peak
  billing-api (prod):       $114    2.1 requests/sec avg
  reporting-api:            ~$20    Lower traffic
  hello-app:                ~$5     Simple service
  jobs-api:                 ~$10    Job submission queue
  jobs-worker:              ~$25    GPU-heavy workload
  
  Subtotal team-alpha:      $150

Team Beta (Lighter usage)
  [services]:               $75

Platform Services (Shared)
  PostgreSQL:               $12     Shared database
  Redis:                    $5      Shared cache
  ArgoCD:                   $8      GitOps platform
  Platform overhead:        $6
  
  Subtotal platform:        $31

TRENDS & ANALYSIS
────────────────
- 12% cost increase vs January (due to new GPU workloads)
- team-alpha cost-per-request is decreasing (efficiency improving)
- Platform cost is well-controlled (shared resources)

OPPORTUNITIES
────────────
1. Right-size dev environment (12% over-provisioned)
2. Reduce staging replicas from 2 to 1 (save ~$15/month)
3. Consolidate Redis instances (currently over-provisioned)

NEXT MONTH FORECAST
───────────────────
Expected cost: $245 (slight decrease with optimizations)
```

### Chargeback (Internal Cost Allocation)

**If using chargeback model:**

```
Team Invoice – February 2026

team-alpha Services:       $119
  billing-api (prod):      $114
  Other services:          $5

Shared Services Allocation: $31
  (1/2 of platform shared cost, assuming equal teams)

TOTAL INVOICE:             $150

Payment Terms: Internal month-end

Notes:
- This is a *virtual* cost allocation
- Used for accountability and optimization
- No actual payment required (internal chargeback)
```

---

## 🎯 Capacity Planning

### Growth Forecasting

**Historical data:**

```
Month       Cost    Growth  Notes
────────────────────────────────
Dec 2025    $180   -       Baseline
Jan 2026    $228   +27%    New team-beta onboarded
Feb 2026    $256   +12%    New GPU workloads
Mar 2026?   $310?  +21%    Projected (3 new services)
```

**Projection:**
```
If linear trend continues:
  - Cost will reach $400/month by June
  - Annual run rate: ~$3,600

If growth accelerates:
  - Could exceed $500/month

Recommendation: Plan hardware refresh or cost controls
```

### Resource Planning

**Current cluster resources:**
```
Nodes:        1 worker node
Total CPU:    4 cores
Total Memory: 8 GB
Utilization:  ~60% (CPU), ~55% (Memory)
Headroom:     40% CPU, 45% Memory
```

**Forecast:**
```
At current growth rate (15% month):
  By June: 85% utilization
  By July: Over capacity

Action: Plan second node addition in May
        (Cost increase: ~$100/month for new hardware)
```

---

## 🔍 Cost Analysis Examples

### Example 1: Why Did Costs Jump?

**Scenario**: Cost spike from $200 to $280 month-over-month

**Investigation**:
1. Check dashboard: which service increased?
   → jobs-worker (GPU workload) increased significantly

2. Check timeline: when did it start?
   → March 1st (new AI project launched)

3. Check metrics: are we utilizing the GPU?
   → CPU usage: 85% (good)
   → Memory usage: 40% (over-provisioned)

**Findings**:
- 3 GPU workers instead of 1 (necessary for job volume)
- GPU node premium applies (expected cost)
- Memory could be right-sized (optimization opportunity)

**Actions**:
- Accept cost (justified by business need)
- Schedule right-sizing for next month

---

### Example 2: Cost vs Business Value

**Service: reporting-api**

```
Monthly Cost:           $22
Queries Processed:      15,000
Cost per Query:         $0.0015

Business Value:         $1,500 (revenue from reports)
ROI:                    68x (extremely valuable)

Decision: Maintain/improve service
```

**Service: demo-api (deprecated)**

```
Monthly Cost:           $8
Queries Processed:      50 (test queries only)
Cost per Query:         $0.16

Business Value:         $0 (demo only)
ROI:                    0x (waste)

Decision: Shut down and redeploy resources
```

---

## 📋 FinOps Best Practices

### Do's ✅

- ✅ Track and monitor cost continuously
- ✅ Align cost with business value
- ✅ Right-size resources based on actual usage
- ✅ Use automation for cost optimization
- ✅ Share cost visibility with teams
- ✅ Include cost in architecture decisions
- ✅ Conduct monthly cost reviews
- ✅ Implement cost controls per environment

### Don'ts ❌

- ❌ Allocate fixed budgets without visibility
- ❌ Over-provision "just in case"
- ❌ Ignore small waste (sums to large amounts)
- ❌ Keep services running that aren't used
- ❌ Fail to review and optimize regularly
- ❌ Make cost decisions without data
- ❌ Penalize teams for cost (foster collaboration instead)

---

## 🛠️ Cost Optimization Roadmap

### Phase 1: Foundation (Done)
- ✅ Establish virtual cost model
- ✅ Implement cost metrics in applications
- ✅ Create cost dashboard in Grafana
- ✅ Define SLA-driven resource requests

### Phase 2: Visibility (Current)
- 🔄 Cost alerts and budget warnings
- 🔄 Monthly cost reports
- 🔄 Per-team cost dashboards
- 🔄 Cost forecasting and trend analysis

### Phase 3: Optimization (Q2 2026)
- 📅 Automated right-sizing recommendations
- 📅 Chargeback model implementation
- 📅 Cost budget enforcement
- 📅 Reserved capacity planning

### Phase 4: Advanced (Q3 2026)
- 📅 ML-driven cost anomaly detection
- 📅 Spot/preemptible instance simulation
- 📅 Multi-cloud cost comparison
- 📅 Cost as a service quality metric

---

## 📚 Related Documents

- [SRE Playbook](./sre-playbook.md) – Includes cost-related alerts
- [Architecture Overview](./architecture/README.md) – Cost considerations in design
- [Environment Strategy](./architecture/environment-strategy.md) – Cost differences by environment

---

## 🎓 Learning Resources

- **Cloud Cost Management**: Google Cloud FinOps guide
- **AWS Cost Optimization**: AWS Well-Architected Framework – Cost Optimization pillar
- **Kubernetes Cost**: Kubecost project documentation

---

*Last updated: February 16, 2026*
