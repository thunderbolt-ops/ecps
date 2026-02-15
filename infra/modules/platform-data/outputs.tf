output "postgres_service_name" {
  description = "Name of the Postgres service in platform-data"
  value       = try(kubernetes_service_v1.postgres[0].metadata[0].name, null)
}

output "redis_service_name" {
  description = "Name of the Redis service in platform-data"
  value       = try(kubernetes_service_v1.redis[0].metadata[0].name, null)
}

output "minio_service_name" {
  description = "Name of the MinIO service in platform-data"
  value       = try(kubernetes_service_v1.minio[0].metadata[0].name, null)
}
