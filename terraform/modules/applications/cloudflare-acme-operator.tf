resource "juju_application" "acme-operator" {
  name  = "acme-operator"
  model = juju_model.test-observer.name

  charm {
    name    = "cloudflare-acme-operator"
    channel = "stable"
  }

  config = {
    cloudflare_dns_api_token       = var.cloudflare_dns_api_token
    cloudflare_zone_read_api_token = var.cloudflare_zone_read_api_token
    email                          = var.cloudflare_email
  }
}
