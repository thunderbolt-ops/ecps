variable "namespace" {
  type        = string
  description = "Namespace to deploy data services into"
}

variable "postgres_enabled" {
  type        = bool
  default     = true
}

variable "redis_enabled" {
  type        = bool
  default     = true
}

variable "minio_enabled" {
  type        = bool
  default     = true
}

variable "postgres_password" {
  type        = string
  sensitive   = true
}

variable "minio_root_user" {
  type        = string
  default     = "minioadmin"
}

variable "minio_root_password" {
  type        = string
  sensitive   = true
}

