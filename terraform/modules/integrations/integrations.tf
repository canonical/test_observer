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
    endpoint = "test-observer-rest-api-v1"
  }

  application {
    name     = juju_application.test-observer-frontend.name
    endpoint = "test-observer-rest-api-v1"
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

resource "juju_integration" "ingress-to-acme-operator" {
    application {
        name = juju_application.ingress.name
        endpoint = "certificates"
    }

    application {
        name = juju_application.cloudflare_acme_operator.name
        endpoint = "certificates"
    }
}