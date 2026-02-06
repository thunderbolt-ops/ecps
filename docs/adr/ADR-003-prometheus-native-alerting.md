# ADR-003: Prometheus-Native Alerting

## Status
Accepted

## Context
Alerting is a core reliability concern.
Two approaches were considered:
- Grafana-managed alerts
- Prometheus-native alerts using PrometheusRule CRDs

Grafana alerts are UI-driven and dashboard-centric.

## Decision
Define alerts using PrometheusRule CRDs evaluated directly by Prometheus.

## Rationale
- Alerts live close to the data source
- Rules are version-controlled and auditable
- Prometheus remains the source of truth
- Grafana is used for visualization only
- Aligns with production SRE practices

## Consequences
- Alerts do not appear in Grafana Alerting UI
- Operators must use Prometheus or Alertmanager views
- Slightly steeper learning curve

This separation is intentional and reinforces correct mental models.
