terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.5"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.25"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
  }
}


provider "kind" {}

/*
module "cluster" {
  source = "../../modules/cluster"

  cluster_name = "ecps-dev"
  worker_count = 1
}
*/

provider "kubernetes" {
  config_path    = pathexpand("~/.kube/config")
  config_context = "kind-ecps-dev"
}

provider "helm" {
  kubernetes {
    config_path    = pathexpand("~/.kube/config")
    config_context = "kind-ecps-dev"
  }
}

