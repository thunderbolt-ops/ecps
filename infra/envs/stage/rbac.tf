#############################
# Service Accounts
#############################

# Platform admin service account (cluster-level admin via binding)
resource "kubernetes_service_account_v1" "platform_admin" {
  metadata {
    name      = "platform-admin"
    namespace = kubernetes_namespace.platform_system.metadata[0].name

    labels = {
      "ecps.io/role" = "platform-admin"
    }
  }
}

# Team Alpha namespace owner
resource "kubernetes_service_account_v1" "team_alpha_dev" {
  metadata {
    name      = "team-alpha-dev"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name

    labels = {
      "ecps.io/role" = "team-owner"
      "ecps.io/team" = "team-alpha"
    }
  }
}

# Team Beta namespace owner
resource "kubernetes_service_account_v1" "team_beta_dev" {
  metadata {
    name      = "team-beta-dev"
    namespace = kubernetes_namespace.team_beta.metadata[0].name

    labels = {
      "ecps.io/role" = "team-owner"
      "ecps.io/team" = "team-beta"
    }
  }
}

#############################
# ClusterRoles
#############################

# Admin rights within a namespace (but not cluster-wide)
resource "kubernetes_cluster_role" "team_namespace_admin" {
  metadata {
    name = "ecps-team-namespace-admin"
  }

  rule {
    api_groups = ["*"]
    resources  = ["*"]
    verbs      = ["*"]
  }
}

# Read-only rights within a namespace
resource "kubernetes_cluster_role" "team_namespace_readonly" {
  metadata {
    name = "ecps-team-namespace-readonly"
  }

  rule {
    api_groups = ["*"]
    resources  = ["*"]
    verbs      = ["get", "list", "watch"]
  }
}

#############################
# RoleBindings / ClusterRoleBindings
#############################

# Platform admin mapped to built-in cluster-admin
resource "kubernetes_cluster_role_binding" "platform_admin_cluster_admin" {
  metadata {
    name = "ecps-platform-admin-cluster-admin"
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "cluster-admin"
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.platform_admin.metadata[0].name
    namespace = kubernetes_service_account_v1.platform_admin.metadata[0].namespace
  }
}

# Team Alpha: namespace admin in team-alpha
resource "kubernetes_role_binding" "team_alpha_admin" {
  metadata {
    name      = "team-alpha-admin-binding"
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.team_namespace_admin.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.team_alpha_dev.metadata[0].name
    namespace = kubernetes_namespace.team_alpha.metadata[0].name
  }
}

# Team Beta: namespace admin in team-beta
resource "kubernetes_role_binding" "team_beta_admin" {
  metadata {
    name      = "team-beta-admin-binding"
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.team_namespace_admin.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.team_beta_dev.metadata[0].name
    namespace = kubernetes_namespace.team_beta.metadata[0].name
  }
}
