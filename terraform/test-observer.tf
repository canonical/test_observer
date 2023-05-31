# This is a fully configured provider containing all the 
# relevant information to connect to a Juju controller.
# This information can be collected by checking the local
# juju folder (~/.local/share/juju/), or by querying the
# controller using `juju show-controller --show-password`.
# If you have already installed and configured a local
# Juju CLI or prefer to use a configuration using environment
# variables, you can use an empty provider. See the next
# example for more details.

#provider "juju" {
#  controller_addresses = "10.225.205.241:17070,10.225.205.242:17070"
#
#  username = "jujuuser"
#  password = "password1"
#
#  ca_certificate = file("~/ca-cert.pem")
#}


# When an empty provider is indicated, the Juju
# provider automatically sets the corresponding values
# by checking:
# **First**: the following environment variables that correspond
# to the configuration fields indicated above.
# JUJU_CONTROLLER_ADDRESSES
# JUJU_USERNAME
# JUJU_PASSWORD
# JUJU_CA_CERT
# **Second**: by using a locally installed Juju CLI client.
# This is the most straight-forward solution. Remember, that
# it will use the configuration used by the CLI at that 
# moment. The fields are populated using the output
# from running the command:
# `juju show-controller --show-password`

terraform {
  required_providers {
    juju = {
      version = "~> 0.7.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

resource "juju_model" "test-observer" {
  name = "test-observer-${var.environment}"

  dynamic "cloud" {
    for_each = [var.cloud]
    content {
      name = cloud.value["name"]
      // access more properties as needed
    }
  }
}

variable "environment" {
  description = "The environment to deploy to (dev, stage, prod)"
}

variable "cloud" {
  description = "The cloud configuration"
  type        = map(any)
  default = {
    name = "microk8s"
    // add more properties if needed
  }
}

variable "cloudflare_acme" {
  description = "Control whether Cloudflare ACME operator should be included in the deployment"
  type        = bool
  default     = false
}

variable "cloudflare_dns_api_token" {
  description = "Cloudflare DNS API token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudflare_zone_read_api_token" {
  description = "Cloudflare zone read API token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudflare_email" {
  description = "Cloudflare account email address"
  type        = string
  sensitive   = true
  default     = ""
}

variable "external_ingress_hostname" {
  description = "External hostname for the ingress"
  type        = string
}

resource "juju_application" "ingress" {
  name  = "ingress"
  model = juju_model.test-observer.name

  charm {
    name    = "traefik-k8s"
    channel = "stable"
  }

  config = {
    routing_mode      = "subdomain"
    external_hostname = var.external_ingress_hostname
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
    hostname = "test-observer-api"
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
    hostname                 = "test-observer-frontend"
    test-observer-api-scheme = "http://"
  }

  units = 1
}

resource "juju_application" "acme-operator" {
  name  = "acme-operator"
  model = juju_model.test-observer.name
  count = var.cloudflare_acme ? 1 : 0

  charm {
    name    = "cloudflare-acme-operator"
    channel = "beta"
    series  = "jammy"
  }

  config = {
    cloudflare_dns_api_token       = var.cloudflare_dns_api_token
    cloudflare_zone_read_api_token = var.cloudflare_zone_read_api_token
    email                          = var.cloudflare_email
  }
}

resource "juju_integration" "ingress-to-cloudflare-acme-operator" {
  model = juju_model.test-observer.name
  count = var.cloudflare_acme ? 1 : 0

  application {
    name     = juju_application.ingress.name
    endpoint = "certificates"
  }

  application {
    name     = juju_application.acme-operator[count.index].name
    endpoint = "certificates"
  }
}

resource "juju_integration" "test-observer-api-database-access" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-api.name
    endpoint = "database"
  }

  application {
    name     = juju_application.pg.name
    endpoint = "database"
  }
}

resource "juju_integration" "test-observer-frontend-to-rest-api-v1-access" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-api.name
    endpoint = "test-observer-rest-api"
  }

  application {
    name     = juju_application.test-observer-frontend.name
    endpoint = "test-observer-rest-api"
  }
}

resource "juju_integration" "test-observer-frontend-ingress" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-frontend.name
    endpoint = "ingress"
  }

  application {
    name     = juju_application.ingress.name
    endpoint = "ingress"
  }
}


resource "juju_integration" "test-observer-api-ingress" {
  model = juju_model.test-observer.name

  application {
    name     = juju_application.test-observer-api.name
    endpoint = "ingress"
  }

  application {
    name     = juju_application.ingress.name
    endpoint = "ingress"
  }
}
