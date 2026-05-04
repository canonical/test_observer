resource "juju_application" "test-observer-frontend" {
  count      = var.deploy_test_observer_frontend ? 1 : 0
  model_uuid = data.juju_model.model.uuid
  name       = var.frontend_config.name

  charm {
    name     = "test-observer-frontend"
    channel  = var.frontend_config.channel
    base     = var.frontend_config.base
    revision = var.frontend_config.revision
  }
  config = var.frontend_config.config
  units  = var.frontend_config.units
}

resource "juju_application" "test-observer-api" {
  model_uuid = data.juju_model.model.uuid
  name       = var.api_config.name

  charm {
    name     = "test-observer-api"
    channel  = var.api_config.channel
    base     = var.api_config.base
    revision = var.api_config.revision
  }

  config = var.api_config.config
  units  = var.api_config.units
}

resource "juju_application" "database" {
  count      = var.deploy_database ? 1 : 0
  name       = var.database_config.name
  model_uuid = data.juju_model.model.uuid

  charm {
    name     = "postgresql-k8s"
    channel  = var.database_config.channel
    base     = var.database_config.base
    revision = var.database_config.revision
  }

  config = var.database_config.config
  units  = var.database_config.units
}

#Hardcoded for now, will be replaced with ValKey 
resource "juju_application" "redis" {
  name       = "redis"
  model_uuid = data.juju_model.model.uuid

  charm {
    name     = "redis-k8s"
    channel  = "latest/edge"
    base     = "ubuntu@22.04"
    revision = 27
  }
}