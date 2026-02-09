###############################################
# File: infra/envs/dev/slo-hello-app.tf
#
# Purpose:
#   Apply Prometheus SLO rules for team-alpha hello-app
#   into platform-observability namespace.
###############################################

locals {
  hello_app_slo_rules_yaml = file("${path.root}/../../../sre/rules/hello-app-slo-rules.yaml")
}

resource "kubernetes_manifest" "hello_app_slo_rules" {
  manifest = yamldecode(local.hello_app_slo_rules_yaml)

  # Also requires PrometheusRule CRD from kube-prometheus-stack
  depends_on = [
    helm_release.kube_prometheus_stack
  ]
}
