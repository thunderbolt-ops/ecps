#############################
# TEAM ALPHA NETWORK POLICIES
#############################

# 1. Default deny all ingress to team-alpha
resource "kubernetes_network_policy" "team_alpha_default_deny_ingress" {
  metadata {
    name      = "default-deny-ingress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress"]
  }
}

# 2. Allow ingress from same namespace (team-alpha)
resource "kubernetes_network_policy" "team_alpha_allow_same_namespace_ingress" {
  metadata {
    name      = "allow-same-namespace-ingress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}

    ingress {
      from {
        pod_selector {}
      }
    }

    policy_types = ["Ingress"]
  }
}

# 3. Allow ingress from platform namespaces to team-alpha
resource "kubernetes_network_policy" "team_alpha_allow_platform_ingress" {
  metadata {
    name      = "allow-platform-ingress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}

    ingress {
      from {
        namespace_selector {
          match_labels = {
            "ecps.io/owner" = "platform"
          }
        }
      }
    }

    policy_types = ["Ingress"]
  }
}

# 4. Default deny all egress from team-alpha
resource "kubernetes_network_policy" "team_alpha_default_deny_egress" {
  metadata {
    name      = "default-deny-egress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Egress"]
  }
}

# 5. Allow egress to same namespace (team-alpha)
resource "kubernetes_network_policy" "team_alpha_allow_same_namespace_egress" {
  metadata {
    name      = "allow-same-namespace-egress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        pod_selector {}
      }
    }

    policy_types = ["Egress"]
  }
}

# 5b. Allow egress from team-alpha to platform namespaces (platform-system/data/identity/observability)
resource "kubernetes_network_policy" "team_alpha_allow_platform_egress" {
  metadata {
    name      = "allow-platform-egress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        namespace_selector {
          match_labels = {
            "ecps.io/owner" = "platform"
          }
        }
      }
    }

    policy_types = ["Egress"]
  }
}

# 5c. Allow DNS egress from team-alpha (CoreDNS in kube-system)
resource "kubernetes_network_policy" "team_alpha_allow_dns_egress" {
  metadata {
    name      = "allow-dns-egress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        namespace_selector {
          match_labels = {
            "kubernetes.io/metadata.name" = "kube-system"
          }
        }

        pod_selector {
          match_labels = {
            "k8s-app" = "kube-dns"
          }
        }
      }

      ports {
        protocol = "UDP"
        port     = 53
      }

      ports {
        protocol = "TCP"
        port     = 53
      }
    }

    policy_types = ["Egress"]
  }
}

#############################
# TEAM BETA NETWORK POLICIES
#############################

# 6. Default deny all ingress to team-beta
resource "kubernetes_network_policy" "team_beta_default_deny_ingress" {
  metadata {
    name      = "default-deny-ingress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress"]
  }
}

# 7. Allow ingress from same namespace (team-beta)
resource "kubernetes_network_policy" "team_beta_allow_same_namespace_ingress" {
  metadata {
    name      = "allow-same-namespace-ingress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}

    ingress {
      from {
        pod_selector {}
      }
    }

    policy_types = ["Ingress"]
  }
}

# 8. Allow ingress from platform namespaces to team-beta
resource "kubernetes_network_policy" "team_beta_allow_platform_ingress" {
  metadata {
    name      = "allow-platform-ingress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}

    ingress {
      from {
        namespace_selector {
          match_labels = {
            "ecps.io/owner" = "platform"
          }
        }
      }
    }

    policy_types = ["Ingress"]
  }
}

# 9. Default deny all egress from team-beta
resource "kubernetes_network_policy" "team_beta_default_deny_egress" {
  metadata {
    name      = "default-deny-egress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Egress"]
  }
}

# 10. Allow egress to same namespace (team-beta)
resource "kubernetes_network_policy" "team_beta_allow_same_namespace_egress" {
  metadata {
    name      = "allow-same-namespace-egress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        pod_selector {}
      }
    }

    policy_types = ["Egress"]
  }
}

# 10b. Allow egress from team-beta to platform namespaces (platform-system/data/identity/observability)
resource "kubernetes_network_policy" "team_beta_allow_platform_egress" {
  metadata {
    name      = "allow-platform-egress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        namespace_selector {
          match_labels = {
            "ecps.io/owner" = "platform"
          }
        }
      }
    }

    policy_types = ["Egress"]
  }
}

# 10c. Allow DNS egress from team-beta (CoreDNS in kube-system)
resource "kubernetes_network_policy" "team_beta_allow_dns_egress" {
  metadata {
    name      = "allow-dns-egress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}

    egress {
      to {
        namespace_selector {
          match_labels = {
            "kubernetes.io/metadata.name" = "kube-system"
          }
        }

        pod_selector {
          match_labels = {
            "k8s-app" = "kube-dns"
          }
        }
      }

      ports {
        protocol = "UDP"
        port     = 53
      }

      ports {
        protocol = "TCP"
        port     = 53
      }
    }

    policy_types = ["Egress"]
  }
}

