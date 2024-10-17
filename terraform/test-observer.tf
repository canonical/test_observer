terraform {
  required_providers {
    juju = {
      version = "~> 0.7.0"
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
    stg     = "https://84a48d05b2444e47a7fa176b577bf85a@sentry.is.canonical.com//68",
    development = ""
  }
}

resource "juju_model" "test-observer" {
  name = "test-observer-${var.environment}"
}

resource "juju_application" "ingress" {
  name  = "ingress"
  model = juju_model.test-observer.name
  trust = true

  charm {
    name    = "nginx-ingress-integrator"
    channel = "stable"
  }

  config = {
    tls-secret-name        = var.tls_secret_name
    whitelist-source-range = var.nginx_ingress_integrator_charm_whitelist_source_range
  }
}

resource "juju_application" "pg" {
  name  = "db"
  model = juju_model.test-observer.name
  trust = true

  charm {
    name    = "postgresql-k8s"
    channel = "14/candidate"
    series  = "jammy"
  }
}

resource "juju_application" "test-observer-api" {
  name  = "api"
  model = juju_model.test-observer.name

  charm {
    name    = "test-observer-api"
    channel = "latest/edge"
    series  = "jammy"
  }

  config = {
    hostname   = var.environment == "stg" ? "test-observer-api-staging.${var.external_ingress_hostname}" : "test-observer-api.${var.external_ingress_hostname}"
    port       = var.environment == "development" ? 30000 : 443
    sentry_dsn = "${local.sentry_dsn_map[var.environment]}"
  }

  units = 1
}

resource "juju_application" "test-observer-frontend" {
  name  = "frontend"
  model = juju_model.test-observer.name

  charm {
    name    = "test-observer-frontend"
    channel = "latest/edge"
    series  = "jammy"
  }

  config = {
    hostname                 = var.environment == "stg" ? "test-observer-staging.${var.external_ingress_hostname}" : "test-observer.${var.external_ingress_hostname}"
    test-observer-api-scheme = var.environment == "development" ? "http://" : "https://"
  }

  units = 3
}

resource "juju_application" "redis" {
  name  = "redis"
  model = juju_model.test-observer.name

  charm {
    name    = "redis-k8s"
    channel = "latest/edge"
  }
}

resource "juju_integration" "test-observer-api-database-access" {
  model = juju_model.test-observer.name

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.pg.name
  }
}

resource "juju_integration" "test-observer-frontend-to-rest-api-access" {
  model = juju_model.test-observer.name

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.test-observer-frontend.name
  }
}

resource "juju_integration" "test-observer-frontend-ingress" {
  model = juju_model.test-observer.name

  application {
    name = juju_application.test-observer-frontend.name
  }

  application {
    name = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-api-ingress" {
  model = juju_model.test-observer.name

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-redis-access" {
  model = juju_model.test-observer.name

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.redis.name
  }
}
