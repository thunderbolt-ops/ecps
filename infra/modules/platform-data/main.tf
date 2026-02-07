#################################
# Postgres (official image)
#################################

resource "kubernetes_deployment" "postgres" {
  count = var.postgres_enabled ? 1 : 0

  metadata {
    name      = "postgres"
    namespace = var.namespace
    labels = {
      app = "postgres"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = "postgres:16-alpine"

          port {
            container_port = 5432
          }

          env {
            name  = "POSTGRES_PASSWORD"
            value = var.postgres_password
          }

          # For dev: simple, no persistent volume
          resources {
            requests = {
              cpu    = "20m"
              memory = "64Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  count = var.postgres_enabled ? 1 : 0

  metadata {
    name      = "postgres"
    namespace = var.namespace
    labels = {
      app = "postgres"
    }
  }

  spec {
    selector = {
      app = "postgres"
    }

    port {
      name        = "postgres"
      port        = 5432
      target_port = 5432
    }

    type = "ClusterIP"
  }
}

#################################
# Redis (official image)
#################################

resource "kubernetes_deployment" "redis" {
  count = var.redis_enabled ? 1 : 0

  metadata {
    name      = "redis"
    namespace = var.namespace
    labels = {
      app = "redis"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "redis"
      }
    }

    template {
      metadata {
        labels = {
          app = "redis"
        }
      }

      spec {
        container {
          name  = "redis"
          image = "redis:7-alpine"

          port {
            container_port = 6379
          }

          # Disable persistence for dev (memory-only)
          command = ["redis-server"]
          args    = ["--appendonly", "no"]

          resources {
            requests = {
              cpu    = "10m"
              memory = "32Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "redis" {
  count = var.redis_enabled ? 1 : 0

  metadata {
    name      = "redis"
    namespace = var.namespace
    labels = {
      app = "redis"
    }
  }

  spec {
    selector = {
      app = "redis"
    }

    port {
      name        = "redis"
      port        = 6379
      target_port = 6379
    }

    type = "ClusterIP"
  }
}

#################################
# MinIO (official image)
#################################

resource "kubernetes_deployment" "minio" {
  count = var.minio_enabled ? 1 : 0

  metadata {
    name      = "minio"
    namespace = var.namespace
    labels = {
      app = "minio"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "minio"
      }
    }

    template {
      metadata {
        labels = {
          app = "minio"
        }
      }

      spec {
        container {
          name  = "minio"
          image = "minio/minio:latest"

          # API on :9000, console on :9001
          args = ["server", "/data", "--console-address", ":9001"]

          port {
            container_port = 9000
          }

          port {
            container_port = 9001
          }

          env {
            name  = "MINIO_ROOT_USER"
            value = var.minio_root_user
          }

          env {
            name  = "MINIO_ROOT_PASSWORD"
            value = var.minio_root_password
          }

          resources {
            requests = {
              cpu    = "20m"
              memory = "64Mi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "minio" {
  count = var.minio_enabled ? 1 : 0

  metadata {
    name      = "minio"
    namespace = var.namespace
    labels = {
      app = "minio"
    }
  }

  spec {
    selector = {
      app = "minio"
    }

    port {
      name        = "api"
      port        = 9000
      target_port = 9000
    }

    port {
      name        = "console"
      port        = 9001
      target_port = 9001
    }

    type = "ClusterIP"
  }
}

