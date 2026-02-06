# ADR-001: Use kind for Local Kubernetes Cluster

## Status
Accepted

## Context
ECPS requires a local Kubernetes cluster that:
- Can be created and destroyed quickly
- Runs on a single Ubuntu machine
- Does not depend on cloud credentials
- Behaves similarly to upstream Kubernetes

Options considered:
- Minikube
- kind
- MicroK8s
- K3s

## Decision
Use `kind` (Kubernetes IN Docker) as the local Kubernetes implementation.

## Rationale
- Uses upstream Kubernetes binaries
- Fast cluster creation and teardown
- Well-supported by CNCF ecosystem tools
- Simple networking model for local labs
- Commonly used in CI pipelines

## Consequences
- NodePort networking has limitations
- No built-in NetworkPolicy enforcement guarantees
- Not suitable for performance testing

These trade-offs are acceptable for ECPS, which prioritizes correctness
and architectural clarity over realism.
