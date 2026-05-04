##### DB-S3 Integrations #####
resource "juju_integration" "db-backups-restore" {
  count      = var.deploy_database && var.enable_backups ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.backup-db[0].name
  }

  application {
    name = juju_application.s3-integrator[0].name
  }
}

resource "juju_integration" "db-backups" {
  count      = var.enable_backups ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.database[0].name
  }

  application {
    name = juju_application.s3-integrator[0].name
  }
}

##### API - DB Integration #####
resource "juju_integration" "test-observer-api-database-access" {
  count      = var.deploy_database ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.database[0].name
  }
}

resource "juju_integration" "test-observer-api-external-database-access" {
  count      = var.deploy_database ? 0 : 1
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    offer_url = var.external_database_url
  }
}


##### API - Frontend Integration #####
resource "juju_integration" "test-observer-frontend-to-rest-api-access" {
  count      = var.deploy_test_observer_frontend ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.test-observer-frontend[0].name
  }
}

##### Redis API Integration #####
resource "juju_integration" "test-observer-redis-access" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.redis.name
  }
}

##### OTEL Integrations #####
resource "juju_integration" "otelcol_prod_cos" {
  for_each   = data.juju_offer.cos_offers
  model_uuid = data.juju_model.model.uuid
  application {
    name     = juju_application.otelcol[0].name
    endpoint = local.cos_endpoint_map[each.key]
  }

  application {
    offer_url = each.value.url
  }
}
