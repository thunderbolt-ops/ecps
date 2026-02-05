#############################
# Default deny ingress
#############################

resource "kubernetes_network_policy" "default_deny_ingress_team_alpha" {
  metadata {
    name      = "default-deny-ingress"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress"]
  }
}

resource "kubernetes_network_policy" "default_deny_ingress_team_beta" {
  metadata {
    name      = "default-deny-ingress"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  spec {
    pod_selector {}
    policy_types = ["Ingress"]
  }
}

#############################
# Allow same-namespace traffic
#############################

resource "kubernetes_network_policy" "allow_same_namespace_team_alpha" {
  metadata {
    name      = "allow-same-namespace"
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

resource "kubernetes_network_policy" "allow_same_namespace_team_beta" {
  metadata {
    name      = "allow-same-namespace"
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

#############################
# Allow platform -> apps
#############################

resource "kubernetes_network_policy" "allow_platform_to_team_alpha" {
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

resource "kubernetes_network_policy" "allow_platform_to_team_beta" {
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
