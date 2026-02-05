# RBAC Model (Development Environment)

This document describes the baseline Role-Based Access Control (RBAC)
model for the ECPS development environment.

The goals are:

- Separate platform ownership from application ownership
- Provide isolated team namespaces
- Make access patterns explicit and reproducible

## Personas

1. Platform Admin
   - Owns the platform and shared components
   - Has cluster-wide administrative rights
   - Works primarily in `platform-*` namespaces

2. Team Alpha
   - Owns workloads in the `team-alpha` namespace
   - Has full control within its namespace only
   - No permissions to other team namespaces

3. Team Beta
   - Owns workloads in the `team-beta` namespace
   - Has full control within its namespace only
   - No permissions to other team namespaces

## Implementation Overview

- ServiceAccounts are used to represent each persona inside the cluster.
- ClusterRoles define reusable permission sets.
- RoleBindings and ClusterRoleBindings attach those roles to ServiceAccounts.

This model is first implemented in the `ecps-dev` cluster and will be
replicated (with stricter policies) in stage and prod.
