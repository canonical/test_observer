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
