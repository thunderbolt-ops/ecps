# ADR-0001: Local Multi-Cluster Kubernetes Strategy

## Status
Accepted

## Context

The Enterprise Cloud Platform Simulator (ECPS) is designed to simulate
a real-world enterprise cloud platform on a single Ubuntu machine.

In real enterprises, environments such as development, staging, and
production are isolated using separate Kubernetes clusters, not merely
namespaces.

A decision is required on how to model environment isolation locally
while preserving architectural fidelity.

## Decision

ECPS will use multiple local Kubernetes clusters (one per environment)
implemented using kind (Kubernetes in Docker):

- ecps-dev
- ecps-stage
- ecps-prod

Each cluster represents a distinct environment and has its own control
plane, node lifecycle, and platform services.

## Alternatives Considered

### Single Cluster with Namespaces Only
Pros:
- Lower resource usage
- Simpler local setup

Cons:
- Weak environment isolation
- Does not reflect real enterprise architecture
- Harder to reason about promotion and blast radius

### Multiple Contexts Pointing to Same Cluster
Pros:
- Minimal setup complexity

Cons:
- Illusion of separation without real isolation
- Misleading operational model

## Consequences

Positive:
- Strong alignment with real-world cloud architecture
- Clear environment boundaries
- Better demonstration of Principal-level design thinking

Negative:
- Higher local resource consumption
- Slightly increased operational complexity

This trade-off is accepted in favor of architectural realism.
