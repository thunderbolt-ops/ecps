variable "cluster_name" {
  description = "Name of the kind cluster"
  type        = string
}

variable "worker_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 1
}

variable "node_image" {
  description = "Kind node image"
  type        = string
  default     = "kindest/node:v1.29.2"
}
