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
