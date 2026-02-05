# Cluster Module

This Terraform module is responsible for creating and managing
local Kubernetes clusters used by ECPS.

Responsibilities:
- kind cluster lifecycle
- cluster naming and configuration
- exposing kubeconfig outputs for downstream use

This module is environment-agnostic and consumed by env-specific
Terraform configurations.
