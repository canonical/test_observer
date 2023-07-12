terraform {
  required_providers {
    juju = {
      version = "~> 0.8.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

variable "environment" {
  description = "The environment to deploy to (development, staging, production)"
}

variable "external_ingress_hostname" {
  description = "External hostname for the ingress"
  type        = string
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
}

resource "juju_application" "pg" {
  name  = "pg"
  model = juju_model.test-observer.name

  charm {
    name    = "postgresql-k8s"
    channel = "14/stable"
    series  = "jammy"
  }
}

resource "juju_application" "test-observer-api" {
  name  = "test-observer-api"
  model = juju_model.test-observer.name

  charm {
    name    = "test-observer-api"
    channel = "edge"
    series  = "jammy"
  }

  config = {
    hostname = "test-observer-api-staging"
  }

  units = 1
}

resource "juju_application" "test-observer-frontend" {
  name = "test-observer-frontend"

  model = juju_model.test-observer.name

  charm {
    name    = "test-observer-frontend"
    channel = "edge"
    series  = "jammy"
  }

  config = {
    hostname                 = "test-observer-staging"
    test-observer-api-scheme = "http://"
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
