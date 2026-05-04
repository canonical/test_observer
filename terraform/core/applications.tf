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

resource "juju_application" "backup-db" {
  count = var.enable_backups ? 1 : 0
  name  = "backup-db"
  model_uuid = data.juju_model.model.uuid

  charm {
    name = "postgresql-k8s"
    channel = var.database_config.channel
    base = var.database_config.base
    revision = var.database_config.revision
  }

  config = var.database_config.config
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

resource "juju_application" "s3-integrator" {
  count      = var.enable_backups ? 1 : 0
  name       = "backups-s3-integrator"
  model_uuid = data.juju_model.model.uuid

  charm {
    name     = "s3-integrator"
    channel  = var.s3_backups_config.channel
    revision = var.s3_backups_config.revision
    base     = var.s3_backups_config.base
  }

  config = {
    endpoint     = var.s3_backups_config.config.endpoint
    region       = var.s3_backups_config.config.region
    bucket       = var.s3_backups_config.config.bucket
    path         = var.s3_backups_config.config.path
    s3-uri-style = var.s3_backups_config.config.s3_uri_style
  }
}

resource "juju_application" "otelcol" {
  count      = var.cos_offers != null ? 1 : 0
  name       = "otelcol"
  model_uuid = data.juju_model.model.name
  charm {
    name     = "opentelemetry-collector"
    channel  = var.otelcol_config.channel
    revision = var.otelcol_config.revision
    base     = var.otelcol_config.base
  }
}