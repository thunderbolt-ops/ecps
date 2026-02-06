resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.platform_observability.metadata[0].name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = "61.2.0"

  create_namespace = false

  depends_on = [
    kubernetes_namespace.platform_observability
  ]

  values = [
    yamlencode({
      prometheus = {
        prometheusSpec = {
          retention = "12h"
        }
      }

      grafana = {
        enabled = true

        adminUser     = "admin"
        adminPassword = "admin"

        service = {
          type = "ClusterIP"
        }
      }

      alertmanager = {
        enabled = true
      }

      kubeStateMetrics = {
        enabled = true
      }

      nodeExporter = {
        enabled = true
      }
    })
  ]
}
