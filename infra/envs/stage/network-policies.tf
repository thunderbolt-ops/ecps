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
            "ecps.io/type" = "system"
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
            "ecps.io/type" = "system"
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

