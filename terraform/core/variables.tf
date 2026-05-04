variable "juju_model_uuid" {
  description = "UUID of the Juju model to deploy to"
  type        = string
}
######### API #########
variable "api_config" {
  description = "Full configuration for the test observer front end"
  type = object({
    name     = string
    channel  = string
    base     = optional(string, "ubuntu@22.04")
    units    = optional(number, 3)
    config   = map(string)
    revision = optional(number)
  })
}

######### FRONTEND #########
variable "deploy_test_observer_frontend" {
  description = "Deploy the test observer frontend"
  default     = true
  type        = bool
}

variable "frontend_config" {
  description = "Full configuration for the test observer front end"
  type = object({
    name     = string
    channel  = string
    base     = optional(string, "ubuntu@22.04")
    units    = optional(number, 3)
    config   = map(string)
    revision = optional(number)
  })
  default = null

  validation {
    condition     = !var.deploy_test_observer_frontend || (var.deploy_test_observer_frontend && var.frontend_config != null)
    error_message = "frontend config must be set if deployed"
  }
}

######### DATABASE #########

variable "deploy_database" {
  description = "Deploy a database with the api"
  default     = true
  type        = bool
}


variable "database_config" {
  description = "Full configuration for the test observer database, if not external"
  type = object({
    name     = string
    channel  = string
    base     = optional(string, "ubuntu@22.04")
    units    = number
    config   = map(string)
    revision = optional(number)
  })
  default = null

  validation {
    condition     = !var.deploy_database || (var.deploy_database && var.database_config != null)
    error_message = "database config must be set if deployed"
  }
}

variable "external_database_url" {
  description = "URL of external database charm endpoint to relate to"
  default     = null
  type        = string

  validation {
    condition     = var.deploy_database || (!var.deploy_database && var.external_database_url != null)
    error_message = "Database url must be set if not deploying an internal database"
  }
}

######### Backups #########

variable "enable_backups" {
  description = "Enable database backups"
  type        = bool
  default     = false

  validation {
    condition     = !var.enable_backups || var.deploy_database
    error_message = "enable_backups requires deploy_database to be true"
  }
}

variable "s3_backups_config" {
  description = "Configuration of the S3 buckets backups are stored in"
  type = object({
    name     = string
    channel  = optional(string, "latest/stable")
    base     = optional(string, "ubuntu@22.04")
    revision = optional(number)
    config = object({
      endpoint     = string
      region       = string
      bucket       = string
      path         = string
      s3_uri_style = string
    })
  })
  default = null

  validation {
    condition     = !var.enable_backups || (var.enable_backups && var.s3_backups_config != null)
    error_message = "S3 backup configs must be set if backups are enabled"
  }
}

######### COS #########

variable "cos_offers" {
  description = "Map of COS offers to integrate with, keyed by the application name to integrate with. The value should be the offer URL for the COS offer."
  type = object({
    loki    = optional(string)
    tempo   = optional(string)
    mimir   = optional(string)
    grafana = optional(string)
  })
  default = null
}

variable "otelcol_config" {
  description = "OTel Collector config to use for the charm."
  type = object({
    channel  = optional(string, "2/stable")
    revision = optional(number)
    base     = optional(string, "ubuntu@22.04")
    config   = optional(map(string))
  })
  default = null

  validation {
    condition     = var.cos_offers == null || (var.cos_offers != null && var.otelcol_config != null)
    error_message = "otelcol_config must be set when cos_offers is provided"
  }
}
