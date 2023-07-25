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
  description = "The environment to deploy to (development, staging, production)"
}

variable "tls_secret_name" {
  description = "Secret where the TLS certificate for ingress is stored"
  type        = string
}

resource "juju_model" "test-observer" {
  name = "test-observer-${var.environment}"
}

resource "juju_application" "ingress" {
  model = juju_model.test-observer.name
  trust = true

  charm {
    name    = "nginx-ingress-integrator"
    channel = "stable"
  }

  config = {
    tls-secret-name = var.tls_secret_name
  }
}

resource "juju_application" "pg" {
  model = juju_model.test-observer.name
  trust = true

  charm {
    name    = "postgresql-k8s"
    channel = "14/stable"
    series  = "jammy"
  }
}

resource "juju_application" "test-observer-api" {
  model = juju_model.test-observer.name

  charm {
    name    = "test-observer-api"
    channel = "latest/edge"
    series  = "jammy"
  }

  config = {
    hostname = var.environment == "staging" ? "test-observer-api-staging" : "test-observer-api"
    port = var.environment == "development" ? 30000 : 443
  }

  units = 1
}

resource "juju_application" "test-observer-frontend" {
  model = juju_model.test-observer.name

  charm {
    name    = "test-observer-frontend"
    channel = "latest/edge"
    series  = "jammy"
  }

  config = {
    hostname = var.environment == "staging" ? "test-observer-staging" : "test-observer"
    test-observer-api-scheme = var.environment == "development" ? "http://" : "https://"
  }

  units = 1
}

resource "juju_integration" "test-observer-api-database-access" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-api.name
  }

  application {
    name     = juju_application.pg.name
    endpoint = "database"
  }
}

resource "juju_integration" "test-observer-frontend-to-rest-api-access" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-api.name
    endpoint = "test-observer-rest-api"
  }

  application {
    name     = juju_application.test-observer-frontend.name
  }
}

resource "juju_integration" "test-observer-frontend-ingress" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-frontend.name
  }

  application {
    name     = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-api-ingress" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-api.name
  }

  application {
    name     = juju_application.ingress.name
  }
}
