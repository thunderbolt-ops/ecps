# Network Policy Model (Development Environment)

This document defines the baseline network isolation model for ECPS.

## Goals

- Enforce namespace-level isolation
- Prevent lateral movement between teams
- Allow controlled platform-to-application access

## Baseline Rules

1. All namespaces start with default deny ingress.
2. Pods may communicate freely within the same namespace.
3. Platform namespaces may initiate connections to application namespaces.
4. Application namespaces may not initiate connections to platform namespaces.
5. External ingress is handled explicitly via ingress controllers.

This model is first applied in the development environment and will
be tightened further in staging and production.
