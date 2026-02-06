terraform {
  required_version = ">= 1.3.0"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.10.0"
    }
  }
}

provider "kind" {}

resource "kind_cluster" "ecps_stage" {
  name       = "ecps-stage"
  node_image = "kindest/node:v1.29.2"

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"
    }
  }
}
