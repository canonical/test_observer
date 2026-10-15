# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

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
    condition = (
      (
        var.database.source == "local-model"
        && var.database.name != null && var.database.endpoint != null && var.database.url == null
      )
      || (
        var.database.source == "cross-model"
        && var.database.name == null && var.database.endpoint == null && var.database.url != null
      )
    )
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
    condition = (
      (
        var.redis.source == "local-model"
        && var.redis.name != null && var.redis.endpoint != null && var.redis.url == null
      )
      || (
        var.redis.source == "cross-model"
        && var.redis.name == null && var.redis.endpoint == null && var.redis.url != null
      )
    )
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
    condition = length(
      setsubtract(keys(var.network_endpoint_providers), ["backend", "frontend"])
    ) == 0
    error_message = "Only 'backend' and 'frontend' are allowed as keys for network_endpoint_providers."
  }

  validation {
    condition     = length(var.network_endpoint_providers) <= 2
    error_message = "You can provide a maximum of two network endpoint providers (backend and frontend)."
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
        (app.source == "local-model" && app.name != null && app.endpoint != null && app.url == null) ||
        (app.source == "cross-model" && app.name == null && app.endpoint == null && app.url != null)
      ])
    )
    error_message = "The network endpoint providers must be defined as either local-model (with endpoint) or cross-model (with url) relations"
  }
}
