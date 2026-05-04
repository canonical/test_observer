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
    units    = number
    config   = map(string)
    revision = number
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
    units    = number
    config   = map(string)
    revision = number
  })
  default = null

  validation {
    condition     = var.deploy_test_observer_frontend && var.frontend_config != null
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
    revision = number
  })
  default = null

  validation {
    condition     = var.deploy_database && var.database_config != null
    error_message = "database config must be set if deployed"
  }
}

variable "external_database_url" {
  description = "URL of external database charm endpoint to relate to"
  default     = null
  type        = string

  validation {
    condition     = var.deploy_database == false && var.external_database_url != null
    error_message = "Database url must be set if not deploying an internal database"
  }
}