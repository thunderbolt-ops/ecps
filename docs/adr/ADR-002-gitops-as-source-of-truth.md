# ADR-002: GitOps as the Source of Truth

## Status
Accepted

## Context
The platform needs a consistent, auditable way to manage:
- Platform services
- Application deployments
- Configuration changes
- Rollbacks and recovery

Manual kubectl workflows do not scale and create configuration drift.

## Decision
Adopt GitOps using Argo CD as the single source of truth for all Kubernetes state.

## Rationale
- Declarative, version-controlled configuration
- Clear audit trail of changes
- Automatic drift detection and correction
- Enables safe recovery by reverting Git state
- Aligns with modern platform engineering practices

## Consequences
- Manual kubectl changes are temporary
- Engineers must learn Git-first workflows
- Outages must be simulated via Git, not imperative commands

These constraints are intentional and desirable.
