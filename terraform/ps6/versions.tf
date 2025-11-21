terraform {
  required_version = ">= 1.12.0"
  required_providers {
    juju = {
      version = "~> 0.23.0"
      source  = "juju/juju"
    }
  }
}