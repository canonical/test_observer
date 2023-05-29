resource "juju_application" "ingress" {
  name  = "ingress"
  model = juju_model.test-observer.name

  charm {
    name    = "traefik-k8s"
    channel = "stable"
  }

  config = {
    routing_mode = "subdomain"
  }
}
