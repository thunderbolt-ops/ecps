resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  namespace  = kubernetes_namespace.platform_system.metadata[0].name
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.10.1"

  create_namespace = false

  depends_on = [
    kubernetes_namespace.platform_system
  ]

  values = [
    yamlencode({
      controller = {
        replicaCount = 1

        service = {
          type = "NodePort"
        }

        admissionWebhooks = {
          enabled = true
        }

        metrics = {
          enabled = false
        }
      }
    })
  ]
}
