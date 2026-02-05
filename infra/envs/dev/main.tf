terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.5"
    }
  }
}

provider "kind" {}

module "cluster" {
  source = "../../modules/cluster"

  cluster_name = "ecps-dev"
  worker_count = 1
}

