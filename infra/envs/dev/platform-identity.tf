###############################################
# File: infra/envs/dev/platform-identity.tf
###############################################

module "platform_identity" {
  source = "../../modules/platform-identity"

  # Use the namespace managed in this env
  namespace = kubernetes_namespace.platform_identity.metadata[0].name

  # Ingress host for Keycloak (dev)
  host = "keycloak.platform.local"

  # Dev admin credentials (change if you like)
  admin_username = "admin"
  admin_password = "ChangeMeNow123!"
}
