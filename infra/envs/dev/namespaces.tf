resource "kubernetes_namespace" "platform_system" {
  metadata {
    name = "platform-system"

    labels = {
      "ecps.io/owner" = "platform"
      "ecps.io/type"  = "system"
    }
  }
}

resource "kubernetes_namespace" "platform_data" {
  metadata {
    name = "platform-data"
    labels = {
      "ecps.io/owner" = "platform"
      "ecps.io/type"  = "data"
    }
  }
}


resource "kubernetes_namespace" "platform_observability" {
  metadata {
    name = "platform-observability"

    labels = {
      "ecps.io/owner" = "platform"
      "ecps.io/type"  = "observability"
    }
  }
}

resource "kubernetes_namespace" "team_alpha" {
  metadata {
    name = "team-alpha"

    labels = {
      "ecps.io/owner" = "team-alpha"
      "ecps.io/type"  = "application"
    }
  }
}

resource "kubernetes_namespace" "team_beta" {
  metadata {
    name = "team-beta"

    labels = {
      "ecps.io/owner" = "team-beta"
      "ecps.io/type"  = "application"
    }
  }
}

resource "kubernetes_namespace" "platform_identity" {
  metadata {
    name = "platform-identity"

    labels = {
      "ecps.io/owner" = "platform"
      "ecps.io/type"  = "identity"
    }
  }
}
