variable "environment" {
  description = "The environment to deploy to (development, stg, production)"
}

variable "tls_secret_name" {
  description = "Secret where the TLS certificate for ingress is stored"
  type        = string
  default     = ""
}

variable "nginx_ingress_integrator_charm_whitelist_source_range" {
  description = "Allowed client IP source ranges. The value is a comma separated list of CIDRs."
  type        = string
  default     = ""
}

variable "backups_s3_endpoint" {
  description = "Database backups s3-integrator endpoint"
  type        = string
  default     = ""
}

variable "backups_s3_region" {
  description = "Database backups s3-integrator region"
  type        = string
  default     = ""
}

variable "backups_s3_bucket" {
  description = "Database backups s3-integrator bucket"
  type        = string
  default     = ""
}

variable "backups_s3_path" {
  description = "Database backups s3-integrator path"
  type        = string
  default     = ""
}

variable "backups_s3_uri_style" {
  description = "Database backups s3-integrator uri_style"
  type        = string
  default     = "path"
}

variable "api_hostname" {
  description = "Test Observer API hostname"
  type        = string
}

variable "frontend_hostname" {
  description = "Test Observer front-end hostname"
  type        = string
}

variable "saml_idp_metadata_url" {
  description = "SAML metadata endpoint for the identity provider"
  type        = string
}

variable "saml_sp_cert" {
  description = "SAML service provider X.509 certificate"
  type        = string
}

variable "saml_sp_key" {
  description = "SAML service provider certificate private key"
  type        = string
}

variable "sessions_secret" {
  description = "Randomly generated secret key to use for signing session cookies"
  type        = string
}

variable "ignore_permissions" {
  description = "List of API permissions to ignore for all requests"
  type        = list(string)
}

variable "api_channel" {
  description = "Charmhub channel for the API charm (e.g., 'latest/edge', 'latest/edge/testing-branch')"
  type        = string
  default     = "latest/edge"
}

variable "frontend_channel" {
  description = "Charmhub channel for the frontend charm (e.g., 'latest/edge', 'latest/edge/testing-branch')"
  type        = string
  default     = "latest/edge"
}

variable "enable_issue_sync" {
  description = "Whether to enable periodic syncing of issues from GitHub, Jira, and Launchpad"
  type        = bool
  default     = false
}
