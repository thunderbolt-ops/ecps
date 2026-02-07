output "postgres_service_name" {
  description = "Name of the Postgres service in platform-data"
  value       = try(kubernetes_service.postgres[0].metadata[0].name, null)
}

output "redis_service_name" {
  description = "Name of the Redis service in platform-data"
  value       = try(kubernetes_service.redis[0].metadata[0].name, null)
}

output "minio_service_name" {
  description = "Name of the MinIO service in platform-data"
  value       = try(kubernetes_service.minio[0].metadata[0].name, null)
}
