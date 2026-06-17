variable "juju_model_uuid" {
  description = "UUID of the Juju model to deploy to"
  type        = string
}

variable "database" {
  description = "The API/backend database relation information"
  type = object({
    endpoint = optional(string, null)
    name     = optional(string, null)
    source   = string
    url      = optional(string, null)
  })

  validation {
    condition     = (var.database.source == "local-model" && var.database.endpoint != null && var.database.url == null) || (var.database.source == "cross-model" && var.database.endpoint == null && var.database.url != null)
    error_message = "A database is required, either in the local model or through a cross-model relation"
  }
}

variable "redis" {
  description = "The redis relation information"
  type = object({
    endpoint = optional(string, null)
    name     = optional(string, null)
    source   = string
    url      = optional(string, null)
  })

  validation {
    condition     = (var.redis.source == "local-model" && var.redis.endpoint != null && var.redis.url == null) || (var.redis.source == "cross-model" && var.redis.endpoint == null && var.redis.url != null)
    error_message = "Redis is required, either in the local model or through a cross-model relation"
  }
}

variable "backend" {
  description = "The Test Observer API/backend application"
  type = object({
    name     = string
    base     = optional(string, "ubuntu@22.04")
    channel  = optional(string)
    config   = map(string)
    image    = optional(string, "ghcr.io/canonical/test_observer/api:latest")
    revision = optional(number)
    units    = optional(number, 3)
  })
}

variable "deploy_frontend" {
  description = "Whether to deploy the Test Observer frontend charm"
  type        = bool
  default     = true
}

variable "frontend" {
  description = "The Test Observer frontend application"
  type = object({
    name     = string
    base     = optional(string, "ubuntu@22.04")
    channel  = optional(string)
    config   = map(string)
    image    = optional(string, "ghcr.io/canonical/test_observer/frontend:latest")
    revision = optional(number)
    units    = optional(number, 3)
  })
  default = null

  validation {
    condition     = !var.deploy_frontend || (var.deploy_frontend && var.frontend != null)
    error_message = "The frontend application must be defined if set to deploy"
  }
}

variable "network_endpoint_providers" {
  description = "The network endpoint provider relation information for the backend and frontend"
  type = map(object({
    endpoint = optional(string, null)
    name     = optional(string, null)
    source   = string
    url      = optional(string, null)
  }))
  default = {}

  validation {
    condition = (
      length(var.network_endpoint_providers) != 1
      || (
        length(var.network_endpoint_providers) == 1 && contains(["backend", "frontend"], keys(var.network_endpoint_providers)[0])
      )
    )
    error_message = "If only one network endpoint provider is supplied, it must be keyed by either 'backend' or 'frontend'"
  }

  validation {
    condition = (
      length(var.network_endpoint_providers) != 2
      || (
        contains(keys(var.network_endpoint_providers), "backend") &&
        contains(keys(var.network_endpoint_providers), "frontend")
      )
    )
    error_message = "If both network endpoint providers are supplied, both the 'backend' and 'frontend' keys are required"
  }

  validation {
    condition = (
      length(var.network_endpoint_providers) != 2
      || (
        jsonencode(var.network_endpoint_providers[keys(var.network_endpoint_providers)[0]])
        != jsonencode(var.network_endpoint_providers[keys(var.network_endpoint_providers)[1]])
      )
    )
    error_message = "The backend and frontend need distinct network endpoint providers"
  }

  validation {
    condition = (
      alltrue([
        for provider, app in var.network_endpoint_providers :
        (app.source == "local-model" && app.endpoint != null && app.url == null) ||
        (app.source == "cross-model" && app.endpoint == null && app.url != null)
      ])
    )
    error_message = "The network endpoint providers must be defined as either local-model (with endpoint) or cross-model (with url) relations"
  }
}
