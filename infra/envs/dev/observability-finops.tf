###############################################
# File: infra/envs/dev/observability-finops.tf
#
# Purpose:
#   Apply Prometheus recording rules for virtual cost
#   into platform-observability namespace.
###############################################

locals {
  virtual_cost_rules_yaml = file("${path.root}/../../../sre/rules/virtual-cost-rules.yaml")
}

# resource "kubernetes_manifest" "virtual_cost_rules" {
#   manifest = yamldecode(local.virtual_cost_rules_yaml)
#
#   # Make sure PrometheusRule CRD exists first (installed by kube-prometheus-stack)
#   depends_on = [
#     helm_release.kube_prometheus_stack
#   ]
# }

