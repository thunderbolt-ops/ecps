resource "helm_release" "argocd" {
  name       = "argocd"
  namespace  = kubernetes_namespace.platform_system.metadata[0].name
  chart      = "argo-cd"
  repository = "https://argoproj.github.io/argo-helm"

  # Lightweight, non-HA Argo CD for local dev
  version = "7.5.2"

  create_namespace = false

  # Ensure namespace exists before Helm runs
  depends_on = [
    kubernetes_namespace.platform_system
  ]

  # Minimal values for now; we will tune later
  values = [
    yamlencode({
      controller = {
        replicas = 1
      }
      repoServer = {
        replicas = 1
      }
      server = {
        replicas = 1
        service = {
          type = "ClusterIP"
        }
      }
      applicationSet = {
        replicas = 1
      }
    })
  ]
}
