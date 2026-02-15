# Enterprise Cloud Platform Simulator (ECPS)

**A production-inspired internal cloud platform running on a single Ubuntu machine.**

ECPS demonstrates how a Principal Cloud Architect or Platform Engineer would design and operate a modern, multi-tenant Kubernetes platform—complete with security policies, observability, SRE practices, cost awareness, and batch workload support.

---

## 🎯 Purpose

ECPS is a **laptop-scale but production-style** platform that simulates:

- **Multiple environments** (dev, stage, prod) with different policies
- **Self-service application onboarding** via standardized templates
- **Security & compliance** enforced centrally (RBAC, network policies, pod security)
- **End-to-end observability** (SLOs, error budgets, dashboards, incident management)
- **Cost & capacity awareness** (FinOps metrics, per-team cost tracking)
- **Diverse workloads** (microservices, APIs, batch jobs, AI/ML workers)

It runs entirely on a single Ubuntu machine using `kind` (Kubernetes in Docker), Terraform, and Helm—but follows patterns used in real enterprise internal cloud platforms.

---

## 🏗️ Architecture Overview

### Logical Layers

```
┌─────────────────────────────────────────────────────────────┐
│               Application Layer (Workloads)                 │
│  team-alpha: billing-api, reporting-api, hello-app, ...    │
│  team-beta: example services                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            Platform Services Layer (Shared)                 │
│  Ingress (NGINX) | GitOps (ArgoCD) | Observability        │
│  Identity (Keycloak) | Databases (Postgres, Redis, MinIO)  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer (Kubernetes + IaC)                    │
│  3 Kind clusters (dev/stage/prod) | Terraform | Helm       │
│  RBAC | Network Policies | Resource Controls               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **Kubernetes (Kind)** | Local Kubernetes clusters (3 environments) | ✅ Deployed |
| **Terraform** | Infrastructure as Code (42+ resources) | ✅ Deployed |
| **GitOps (ArgoCD)** | Declarative app & platform deployments | ✅ Running |
| **Prometheus + Grafana** | Metrics, dashboards, SLO tracking | ✅ Running |
| **Keycloak** | OIDC identity provider | ✅ Running |
| **PostgreSQL, Redis, MinIO** | Shared data services | ✅ Running |
| **Network Policies** | Zero-trust namespace isolation | ✅ Enforced |
| **RBAC** | Role-based access control | ✅ Configured |

---

## 🚀 Quick Start

### Prerequisites

- Ubuntu (native or WSL2)
- Docker (4GB+ RAM recommended)
- kubectl, helm, terraform, kind installed

### Deploy ECPS in 5 Minutes

```bash
# 1. Clone and navigate
git clone https://github.com/thunderbolt-ops/ecps.git
cd ecps

# 2. Provision infrastructure (Terraform)
cd infra/envs/dev
terraform init
terraform apply -auto-approve

# 3. Access services locally (in another terminal)
bash access-services.sh
```

### Access Services

Once running, open your browser to:

- **hello-app**: http://localhost:8080
- **billing-api**: http://localhost:8081
- **jobs-api**: http://localhost:8082
- **reporting-api**: http://localhost:8083

Or use the terminal:

```bash
curl http://localhost:8080/          # → "hello from team alpha"
curl http://localhost:8081/get       # → JSON response
curl http://localhost:8082/status/200  # → HTTP 200
```

For detailed access options, see [SERVICE_ACCESS_EXPLAINED.md](SERVICE_ACCESS_EXPLAINED.md).

---

## 📚 Documentation Structure

### Architecture & Design

- **[Architecture Overview](docs/architecture/README.md)** – High-level platform design
- **[Environment Strategy](docs/architecture/environment-strategy.md)** – dev/stage/prod differences and promotion paths
- **[RBAC Model](docs/architecture/rbac-model.md)** – Identity and access control
- **[Network Policy Model](docs/architecture/network-policy-model.md)** – Zero-trust isolation
- **[Observability Architecture](docs/architecture/observability-architecture.md)** – Metrics, dashboards, SLOs

### Architecture Decision Records (ADRs)

- **[ADR-001: Local Multi-Cluster Kubernetes Strategy](docs/adr/ADR-0001-local-multi-cluster.md)**
- **[ADR-002: Use Kind for Local Kubernetes](docs/adr/ADR-001-use-kind-for-local-kubernetes.md)**
- **[ADR-003: GitOps as Source of Truth](docs/adr/ADR-002-gitops-as-source-of-truth.md)**
- **[ADR-004: Prometheus-Native Alerting](docs/adr/ADR-003-prometheus-native-alerting.md)**

### Operations & SRE

- **[SRE Playbook](docs/sre-playbook.md)** – SLOs, error budgets, on-call expectations
- **[Runbooks](docs/runbooks/README.md)** – Operational procedures (deployment, scaling, incident response)
- **[FinOps Model](docs/finops-notes.md)** – Cost tracking, capacity planning, optimization
- **[AI/Batch Architecture](docs/ai-batch-architecture.md)** – Job scheduling, worker patterns

### Getting Started

- **[QUICKSTART.md](QUICKSTART.md)** – 30-second start guide
- **[BROWSER_ACCESS_GUIDE.md](BROWSER_ACCESS_GUIDE.md)** – All ways to access services
- **[SERVICE_ACCESS_EXPLAINED.md](SERVICE_ACCESS_EXPLAINED.md)** – DNS and networking concepts

---

## 🔧 Technology Stack

### Infrastructure

- **Kubernetes**: kind (1.28.1)
- **Container Runtime**: Docker/containerd
- **IaC**: Terraform v1.9.8
- **Package Manager**: Helm v3.x

### Platform Components

- **Ingress**: NGINX Ingress Controller
- **GitOps**: ArgoCD v2.12.3
- **Observability**: Prometheus Operator, kube-prometheus-stack
- **Identity**: Keycloak (OIDC)
- **Storage**: MinIO (S3-like), PostgreSQL 15, Redis 7

### Security & Policy

- **RBAC**: Kubernetes native
- **Network Policies**: Enforced at namespace level
- **Pod Security**: Restrictions on privileged containers, resource limits
- **OPA Gatekeeper** (planned): Policy-as-code enforcement

### Applications

- **runtime**: Python 3.10+, FastAPI
- **Instrumentation**: Prometheus client library, OpenTelemetry support
- **Testing**: pytest, integration tests via curl

---

## 📊 Key Features Demonstrated

### 1. **Multi-Environment Design**

| Aspect | Dev | Stage | Prod |
|--------|-----|-------|------|
| **Resource Limits** | Relaxed | Medium | Strict |
| **Policy Enforcement** | Loose | Moderate | Strict |
| **SLO Monitoring** | Enabled | Enabled | Enforced |
| **Replicas** | 1x | 2x | 3x+ |

### 2. **Security & Compliance**

- ✅ **Namespace Isolation**: Teams separated by RBAC + network policies
- ✅ **OIDC Integration**: Keycloak as identity provider
- ✅ **Pod Security**: No root containers, mandatory resource limits
- ✅ **Network Policies**: Default-deny + explicit allows
- ✅ **Audit Trail**: Deployment and policy violations logged

### 3. **Observability & SRE**

- ✅ **SLOs**: Latency, availability, error budget tracking
- ✅ **Metrics**: Prometheus scrapes app and infrastructure metrics
- ✅ **Dashboards**: Grafana visualizations
- ✅ **Alerts**: FirePrometheusRules defined in code
- ✅ **Incident Management**: Sample post-mortems and playbooks

### 4. **Cost & Capacity**

- ✅ **Cost Model**: Virtual pricing per CPU/memory
- ✅ **Per-Team Tracking**: Cost breakdown by team and environment
- ✅ **Capacity Planning**: Resource utilization metrics
- ✅ **FinOps Dashboards**: Cost trends and optimization opportunities

### 5. **Batch & AI Workloads**

- ✅ **Job API**: Accepts job submissions
- ✅ **Job Worker**: Processes background jobs from queue
- ✅ **Node Scheduling**: Labeled nodes for "GPU" workloads (simulated)
- ✅ **Observability**: Job latency, success/failure rates

### 6. **GitOps & IaC**

- ✅ **Terraform**: 42+ resources, modular design
- ✅ **ArgoCD**: Continuous deployment from Git
- ✅ **Helm**: Package management for platform services
- ✅ **Self-Service**: Application templates for team onboarding

---

## 🎯 Use Cases

### Platform Team
**Goal**: Design and operate a secure, reliable platform

- ✅ Provision clusters with Terraform
- ✅ Deploy platform services (databases, identity, observability)
- ✅ Define and enforce security policies
- ✅ Monitor platform health and capacity

### Application Teams
**Goal**: Deploy services without infrastructure expertise

- ✅ Onboard new services via self-service templates
- ✅ Use standardized deployment patterns
- ✅ Benefit from shared platform services
- ✅ Monitor service health via provided dashboards

### SREs
**Goal**: Ensure reliability and respond to incidents

- ✅ Define SLOs and error budgets
- ✅ Monitor dashboards in real-time
- ✅ Respond to alerts and incidents
- ✅ Document post-mortems and runbooks

### Security & Compliance
**Goal**: Enforce policies and audit access

- ✅ Define RBAC and network isolation
- ✅ Enforce pod security standards
- ✅ Control image registries and configurations
- ✅ Audit all deployments

---

## 📁 Repository Structure

```
ecps/
├── README.md                          # This file
├── QUICKSTART.md                      # 30-second getting started
├── BROWSER_ACCESS_GUIDE.md            # Access methods explained
├── SERVICE_ACCESS_EXPLAINED.md        # DNS and networking
├── access-services.sh                 # Port-forward automation
│
├── docs/
│   ├── architecture/                  # Design and reference architecture
│   │   ├── README.md
│   │   ├── environment-strategy.md
│   │   ├── rbac-model.md
│   │   ├── network-policy-model.md
│   │   └── observability-architecture.md
│   │
│   ├── adr/                           # Architecture Decision Records
│   │   ├── ADR-0001-local-multi-cluster.md
│   │   ├── ADR-002-gitops-as-source-of-truth.md
│   │   └── ...
│   │
│   ├── runbooks/                      # Operational procedures
│   │   ├── deployment-troubleshooting.md
│   │   ├── incident-response.md
│   │   └── scaling-guide.md
│   │
│   └── sre-playbook.md                # SLO, alert, incident procedures
│
├── infra/                             # Infrastructure as Code (Terraform)
│   ├── envs/
│   │   ├── dev/                       # Development environment
│   │   ├── stage/                     # Staging environment
│   │   └── prod/                      # Production environment (skeleton)
│   │
│   └── modules/                       # Reusable Terraform modules
│       ├── cluster/
│       ├── platform-data/
│       └── platform-identity/
│
├── platform/                          # Platform services
│   ├── gitops/                        # ArgoCD application definitions
│   ├── idp/                           # Internal Developer Platform
│   └── policies/                      # Security & governance policies
│
├── apps/                              # Application workloads
│   ├── team-alpha/
│   │   ├── billing-api/               # Billing microservice (with DB)
│   │   ├── jobs-api/                  # Job submission API
│   │   ├── jobs-worker/               # Batch job processor
│   │   ├── reporting-api/             # Analytics API
│   │   └── hello-app/                 # Simple HTTP service
│   │
│   └── team-beta/                     # Second team (templates)
│
├── sre/                               # SRE artifacts
│   ├── slos/                          # SLO definitions
│   ├── dashboards/                    # Grafana dashboard definitions
│   ├── rules/                         # PrometheusRule definitions
│   ├── alerts/                        # Alert configurations
│   └── incidents/                     # Incident reports & post-mortems
│
└── scripts/                           # Utility scripts
    ├── up-kind-ecps.sh
    └── ...
```

---

## 🔐 Security Highlights

### Multi-Layer Security

1. **Network Isolation**
   - Default-deny network policies
   - Team namespaces isolated from each other
   - Platform-to-app communication explicitly allowed

2. **Access Control**
   - RBAC prevents cross-team access
   - ServiceAccounts with minimal permissions
   - Keycloak for OIDC-based identity

3. **Pod Security**
   - No privileged containers
   - Mandatory resource limits
   - Read-only root filesystem (configurable)

4. **Image Security**
   - Approved registry paths only
   - No "latest" tags in production
   - Image pull secrets configured

---

## 📈 Observability Features

### Metrics & Dashboards

- **Service Dashboards**: Latency, error rate, throughput per service
- **Infrastructure Dashboards**: CPU, memory, disk, network utilization
- **Cost Dashboard**: Per-team and per-environment cost breakdown

### SLOs & Alerts

- **Service SLOs**: Availability and latency targets
- **Error Budget**: Tracking and consumption alerts
- **Burn Rate Alerts**: Multi-window (1h, 6h, 30d) for fast response

### Incident Management

- **Runbooks**: Step-by-step procedures for common issues
- **Post-Mortems**: Templates and examples for incident documentation
- **Blameless Culture**: Focus on systemic improvements

---

## 🤖 Batch & AI Workload Support

ECPS includes a complete batch processing system:

- **jobs-api**: Accepts job submissions via REST API
- **jobs-worker**: Consumes jobs from queue, processes asynchronously
- **Node Scheduling**: Workers scheduled to "GPU" nodes (simulated via labels)
- **Observability**: Queue depth, processing latency, success/failure rates
- **Cost Tracking**: Higher virtual cost for "GPU" resource usage

Example workflow:

```bash
# Submit a job
curl -X POST http://localhost:8082/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"type": "analytics", "params": {"days": 7}}'

# Job is queued and processed by workers
# Status can be checked via API
```

---

## 🎓 Learning Outcomes

By exploring ECPS, you'll understand:

### Cloud Architecture
- Multi-environment design patterns
- Landing zone and namespace isolation concepts
- Shared platform services architecture

### Kubernetes & Container Platforms
- Cluster bootstrapping and lifecycle
- Namespace-based multi-tenancy
- RBAC and network policies
- Helm package management

### Infrastructure as Code
- Terraform modules and composition
- Environment-specific configurations
- State management and best practices

### GitOps & CI/CD
- ArgoCD configuration management
- Self-service application deployment
- Infrastructure and application version control

### SRE & Observability
- SLO definition and tracking
- Error budget management
- Prometheus metrics and Grafana dashboards
- Incident response procedures

### Security
- Zero-trust network architecture
- Pod security standards
- OIDC and identity integration
- Policy-as-code with OPA Gatekeeper

### FinOps & Cost Management
- Cost attribution per team/service
- Capacity planning and optimization
- Virtual cost models and chargeback

---

## 🚦 Current Status

| Component | Status | Details |
|-----------|--------|---------|
| **Infrastructure** | ✅ Complete | 42 Terraform resources, 6 namespaces |
| **Platform Services** | ✅ Complete | PostgreSQL, Redis, MinIO, Keycloak, ArgoCD |
| **Applications** | ✅ Deployed | 5 services (hello-app, billing-api, jobs-api, jobs-worker, reporting-api) |
| **Observability** | ✅ Running | Prometheus, Grafana, AlertManager |
| **RBAC & Policies** | ✅ Enforced | 8 RBAC rules, 16 network policies |
| **SLOs & Alerts** | ✅ Defined | Service-level objectives and burn rate alerts |
| **Documentation** | ✅ Comprehensive | Architecture, ADRs, runbooks, SRE playbook |
| **Batch Workloads** | ✅ Functional | Job submission and worker processing |
| **Cost Tracking** | ✅ Metrics | Per-team and per-environment cost attribution |
| **OPA Gatekeeper** | 🔄 Planned | Policy-as-code enforcement examples |

---

## 🔄 Next Steps

### For Learning
1. Read [Architecture Overview](docs/architecture/README.md)
2. Explore [SRE Playbook](docs/sre-playbook.md) for operational patterns
3. Review [ADRs](docs/adr/) for design decisions
4. Walk through [Runbooks](docs/runbooks/) for operational procedures

### For Enhancement
1. Implement OPA Gatekeeper policies
2. Add OpenTelemetry instrumentation to applications
3. Extend batch job system with real ML workload simulation
4. Create ecpsctl CLI tool for self-service onboarding

### For Portfolio/Interview
- Use this as a flagship project demonstrating Principal-level skills
- Reference specific architecture decisions and trade-offs
- Discuss security, reliability, and cost considerations
- Share incident simulations and post-mortems

---

## 🤝 Contributing

ECPS is a personal learning project, but feel free to fork and extend it:

- Add new application services
- Implement OPA Gatekeeper policies
- Create additional incident scenarios
- Extend cost model and dashboards
- Add compliance checking examples

---

## 📖 References & Further Reading

- **Kubernetes**: https://kubernetes.io/docs/
- **Terraform**: https://www.terraform.io/docs/
- **ArgoCD**: https://argo-cd.readthedocs.io/
- **Prometheus**: https://prometheus.io/docs/
- **SRE Book**: https://sre.google/sre-book/
- **Keycloak**: https://www.keycloak.org/documentation

---

## 📄 License

This project is shared for educational and portfolio purposes.

---

## 📞 Contact & Questions

This project demonstrates hands-on expertise in:
- **Principal Cloud Architecture**
- **Platform Engineering**
- **SRE & Reliability**
- **Cloud Security**
- **FinOps**

Use it to discuss your architectural thinking and engineering practices.

---

## 🎉 Summary

ECPS is a **complete, production-inspired platform** running on a single machine. It demonstrates how modern infrastructure teams:

- ✅ Design secure, multi-environment platforms
- ✅ Enforce policies and governance
- ✅ Ensure reliability through SLOs and observability
- ✅ Enable self-service application deployment
- ✅ Track costs and optimize resource usage
- ✅ Support diverse workloads (APIs, batch jobs, AI/ML)

**Start exploring**: [QUICKSTART.md](QUICKSTART.md) → [Architecture Overview](docs/architecture/README.md) → [SRE Playbook](docs/sre-playbook.md)

---

*Last updated: February 16, 2026*
