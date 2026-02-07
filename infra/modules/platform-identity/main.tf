###############################################
# File: infra/modules/platform-identity/main.tf
###############################################

variable "namespace" {
  description = "Namespace where Keycloak will be deployed"
  type        = string
}

variable "host" {
  description = "Ingress host for Keycloak"
  type        = string
}

variable "admin_username" {
  description = "Keycloak admin username"
  type        = string
  default     = "admin"
}

variable "admin_password" {
  description = "Keycloak admin password"
  type        = string
  sensitive   = true
}

###############################################
# Service Account (optional for future RBAC)
###############################################

resource "kubernetes_service_account" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels = {
      app = "keycloak"
    }
  }
}

###############################################
# Secret for admin credentials (password only)
###############################################

resource "kubernetes_secret" "keycloak_admin" {
  metadata {
    name      = "keycloak-admin-credentials"
    namespace = var.namespace
    labels = {
      app = "keycloak"
    }
  }

  type = "Opaque"

  # kubernetes provider will base64-encode these values for us
  data = {
    password = var.admin_password
  }
}

###############################################
# Deployment: Keycloak (dev mode, in-memory DB)
###############################################

resource "kubernetes_deployment" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels = {
      app = "keycloak"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "keycloak"
      }
    }

    template {
      metadata {
        labels = {
          app = "keycloak"
        }
      }

      spec {
        service_account_name = kubernetes_service_account.keycloak.metadata[0].name

        container {
          name  = "keycloak"
          image = "quay.io/keycloak/keycloak:24.0"

          # Dev mode, in-memory DB (sufficient for dev/OIDC flows)
          args = [
            "start-dev"
          ]

          port {
            name           = "http"
            container_port = 8080
          }

          env {
            name  = "KEYCLOAK_ADMIN"
            value = var.admin_username
          }

          env {
            name = "KEYCLOAK_ADMIN_PASSWORD"

            value_from {
              secret_key_ref {
                name = kubernetes_secret.keycloak_admin.metadata[0].name
                key  = "password"
              }
            }
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }

            # You can add limits here later if needed
          }

          liveness_probe {
            http_get {
              path = "/"
              port = "http"
            }

            initial_delay_seconds = 30
            period_seconds        = 15
          }

          readiness_probe {
            http_get {
              path = "/"
              port = "http"
            }

            initial_delay_seconds = 20
            period_seconds        = 10
          }
        }
      }
    }
  }
}

###############################################
# Service: Keycloak
###############################################

resource "kubernetes_service" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels = {
      app = "keycloak"
    }
  }

  spec {
    selector = {
      app = "keycloak"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 8080
    }

    type = "ClusterIP"
  }
}

###############################################
# Ingress: Keycloak via ingress-nginx
###############################################

resource "kubernetes_ingress_v1" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = var.namespace
    labels = {
      app = "keycloak"
    }

    annotations = {
      "nginx.ingress.kubernetes.io/backend-protocol" = "HTTP"
    }
  }

  spec {
    # Adjust if your ingress class has a different name
    ingress_class_name = "nginx"

    rule {
      host = var.host

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.keycloak.metadata[0].name

              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }
}
