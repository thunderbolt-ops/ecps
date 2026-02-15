###############################################
# Apply billing-api SLO PrometheusRule
###############################################

locals {
  billing_api_slo_rules_yaml = file("${path.root}/../../../sre/rules/billing-api-slo-rules.yaml")
}

# resource "kubernetes_manifest" "billing_api_slo_rules" {
#   manifest = yamldecode(local.billing_api_slo_rules_yaml)
#
#   depends_on = [
#     helm_release.kube_prometheus_stack
#   ]
# }
