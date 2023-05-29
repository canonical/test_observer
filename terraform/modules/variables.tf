provider "juju" {}

variable "model_name" {
  description = "The name of the Juju model to manage"
  type        = string
}

variable "cloud" {
  description = "The cloud configuration"
  type        = map(any)
  default = {
    name = "microk8s"
    // add more properties if needed
  }
}

variable "cloudflare_dns_api_token" {
  description = "Cloudflare DNS API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_read_api_token" {
  description = "Cloudflare zone read API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_email" {
  description = "Cloudflare account email address"
  type        = string
  sensitive   = true
}
