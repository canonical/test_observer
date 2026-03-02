# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

terraform {
  required_providers {
    juju = {
      version = "~> 0.10.1"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

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



locals {
  sentry_dsn_map = {
    production  = "https://dd931d36e0c24681aaeed6abd312c896@sentry.is.canonical.com//66"
    stg         = "https://84a48d05b2444e47a7fa176b577bf85a@sentry.is.canonical.com//68",
    development = ""
  }
  juju_model = "test-observer-${var.environment}"
}

resource "juju_application" "ingress" {
  name  = "ingress"
  model = local.juju_model
  trust = true

  charm {
    name     = "nginx-ingress-integrator"
    channel  = "latest/stable"
    revision = 59
  }

  config = {
    tls-secret-name        = var.tls_secret_name
    whitelist-source-range = var.nginx_ingress_integrator_charm_whitelist_source_range
  }
}

resource "juju_application" "pg" {
  name  = "db"
  model = local.juju_model
  trust = true

  charm {
    name     = "postgresql-k8s"
    channel  = "14/stable"
    base     = "ubuntu@22.04"
    revision = 281
  }

  config = {
    # NOTE: idle_in_transaction_session_timeout is not exposed by postgresql-k8s 14/stable
    # It must be set manually via: ALTER SYSTEM SET idle_in_transaction_session_timeout = '10min';

    # Log queries taking longer than 1 second (in milliseconds)
    # Helps identify performance bottlenecks
    logging_log_min_duration_statement = 1000

    # Log when queries wait for locks
    # Helps identify blocking queries
    logging_log_lock_waits = true
  }
}

resource "juju_application" "backup-restoring-db" {
  name  = "backup-restoring-db"
  model = local.juju_model
  trust = true

  charm {
    name     = "postgresql-k8s"
    channel  = "14/stable"
    base     = "ubuntu@22.04"
    revision = 281
  }

  config = {
    # NOTE: idle_in_transaction_session_timeout is not exposed by postgresql-k8s 14/stable
    # It must be set manually via: ALTER SYSTEM SET idle_in_transaction_session_timeout = '10min';

    # Log queries taking longer than 1 second (in milliseconds)
    # Helps identify performance bottlenecks
    logging_log_min_duration_statement = 1000

    # Log when queries wait for locks
    # Helps identify blocking queries
    logging_log_lock_waits = true
  }
}

resource "juju_application" "test-observer-api" {
  name  = "api"
  model = local.juju_model

  charm {
    name    = "test-observer-api"
    channel = var.api_channel
    base    = "ubuntu@22.04"
  }

  config = {
    hostname              = var.api_hostname
    frontend_hostname     = var.frontend_hostname
    port                  = var.environment == "development" ? 80 : 443
    sentry_dsn            = "${local.sentry_dsn_map[var.environment]}"
    saml_idp_metadata_url = var.saml_idp_metadata_url
    saml_sp_cert          = var.saml_sp_cert
    saml_sp_key           = var.saml_sp_key
    sessions_secret       = var.sessions_secret
    ignore_permissions    = join(",", var.ignore_permissions)
    enable_issue_sync     = var.enable_issue_sync
  }

  units = 3
}

resource "juju_application" "test-observer-frontend" {
  name  = "frontend"
  model = local.juju_model

  charm {
    name    = "test-observer-frontend"
    channel = var.frontend_channel
    base    = "ubuntu@22.04"
  }

  config = {
    hostname                 = var.frontend_hostname
    test-observer-api-scheme = var.environment == "development" ? "http://" : "https://"
  }

  units = 3
}

resource "juju_application" "redis" {
  name  = "redis"
  model = local.juju_model

  charm {
    name     = "redis-k8s"
    channel  = "latest/edge"
    base     = "ubuntu@22.04"
    revision = 27
  }
}

resource "juju_application" "s3-integrator" {
  name  = "backups-s3-integrator"
  model = local.juju_model

  charm {
    name     = "s3-integrator"
    channel  = "latest/stable"
    revision = 77
    base     = "ubuntu@22.04"
  }

  config = {
    endpoint     = var.backups_s3_endpoint
    region       = var.backups_s3_region
    bucket       = var.backups_s3_bucket
    path         = var.backups_s3_path
    s3-uri-style = var.backups_s3_uri_style
  }
}

resource "juju_integration" "db-backups" {
  model = local.juju_model

  application {
    name = juju_application.pg.name
  }

  application {
    name = juju_application.s3-integrator.name
  }
}

resource "juju_integration" "db-backups-restore" {
  model = local.juju_model

  application {
    name = juju_application.backup-restoring-db.name
  }

  application {
    name = juju_application.s3-integrator.name
  }
}

resource "juju_integration" "test-observer-api-database-access" {
  model = local.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.pg.name
  }
}

resource "juju_integration" "test-observer-frontend-to-rest-api-access" {
  model = local.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.test-observer-frontend.name
  }
}

resource "juju_integration" "test-observer-frontend-ingress" {
  model = local.juju_model

  application {
    name = juju_application.test-observer-frontend.name
  }

  application {
    name = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-api-ingress" {
  model = local.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-redis-access" {
  model = local.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.redis.name
  }
}
