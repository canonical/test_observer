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
  }
}

resource "juju_application" "test-observer-api" {
  name  = "api"
  model = local.juju_model

  charm {
    name    = "test-observer-api"
    channel = "latest/edge"
    base    = "ubuntu@22.04"
  }

  config = {
    hostname   = var.environment == "stg" ? "test-observer-api-staging.${var.external_ingress_hostname}" : "test-observer-api.${var.external_ingress_hostname}"
    port       = var.environment == "development" ? 80 : 443
    sentry_dsn = "${local.sentry_dsn_map[var.environment]}"
  }

  units = 1
}

resource "juju_application" "test-observer-frontend" {
  name  = "frontend"
  model = local.juju_model

  charm {
    name    = "test-observer-frontend"
    channel = "latest/edge"
    base    = "ubuntu@22.04"
  }

  config = {
    hostname                 = var.environment == "stg" ? "test-observer-staging.${var.external_ingress_hostname}" : "test-observer.${var.external_ingress_hostname}"
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
