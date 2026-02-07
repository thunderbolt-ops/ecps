module "platform_data" {
  source = "../../modules/platform-data"

  namespace = kubernetes_namespace.platform_data.metadata[0].name

  postgres_password   = "dev-postgres-password"
  minio_root_user     = "minioadmin"
  minio_root_password = "dev-minio-password"

  postgres_enabled = true
  redis_enabled    = true
  minio_enabled    = true
}

