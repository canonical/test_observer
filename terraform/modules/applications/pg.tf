resource "juju_application" "pg" {
  name  = "pg"
  model = juju_model.test-observer.name

  charm {
    name    = "postgresql-k8s"
    channel = "14/stable"
    series  = "jammy"
  }
}
