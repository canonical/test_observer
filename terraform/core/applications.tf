resource "juju_application" "backend" {
  charm {
    name     = "test-observer-api"
    base     = var.backend.base
    channel  = var.backend.channel
    revision = var.backend.revision
  }

  config     = var.backend.config
  model_uuid = data.juju_model.model.uuid
  name       = var.backend.name
  units      = var.backend.units

  resources = {
    "api-image" : var.backend.image
  }
}

resource "juju_application" "frontend" {
  charm {
    name     = "test-observer-frontend"
    base     = var.frontend.base
    channel  = var.frontend.channel
    revision = var.frontend.revision
  }

  config     = var.frontend.config
  count      = var.deploy_frontend ? 1 : 0
  model_uuid = data.juju_model.model.uuid
  name       = var.frontend.name
  units      = var.frontend.units

  resources = {
    "frontend-image" : var.frontend.image
  }
}
