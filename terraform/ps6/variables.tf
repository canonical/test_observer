variable "juju_model" {
  description = "name of juju model"
  type        = string
}

variable "environment" {
  description = "The environment to deploy to (development, stg, production)"
  type        = string
}

variable "config_dir" {
  description = "Directory containing config files"
  type        = string
}

variable "lego_server" {
  description = "Url to server providing lego certificates"
  type        = string
  default     = "https://lego-certs.canonical.com"
}

variable "lego_email" {
  description = "Email address for lego charm"
  type        = string
  default     = "is-admin@canonical.com"
}

variable "lego_plugin" {
  description = "Plugin to use in the lego charm"
  type        = string
  default     = "httpreq"
}

variable "pg_storage_size" {
  description = "Size of storage partition for postgres database"
  type        = string
  default     = "50G"
}

variable "external_ingress_hostname" {
  description = "External hostname for the ingress"
  type        = string
  default     = "canonical.com"
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
  description = "test observer api hostname"
  type        = string
}

variable "api_port" {
  description = "test observer api port"
  type        = number
  default     = 443
}

variable "sentry_dsn" {
  description = "sentry dsn url"
  type        = string
}

variable "frontend_hostname" {
  description = "hostname for frontend"
  type        = string
}

variable "api_scheme" {
  description = "Scheme for api, either http:// or https://"
  type        = string
  default     = "https://"
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
