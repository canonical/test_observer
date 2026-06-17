# Database and redis relations are required for the API/backend
resource "juju_integration" "backend_database" {
  model_uuid = data.juju_model.model.uuid

  application {
    name     = juju_application.backend.name
    endpoint = "database"
  }

  application {
    name      = var.database.source == "local-model" ? var.database.name : null
    endpoint  = var.database.source == "local-model" ? var.database.endpoint : null
    offer_url = var.database.source == "cross-model" ? var.database.url : null
  }
}

resource "juju_integration" "backend_redis" {
  model_uuid = data.juju_model.model.uuid

  application {
    name     = juju_application.backend.name
    endpoint = "redis"
  }

  application {
    name      = var.redis.source == "local-model" ? var.redis.name : null
    endpoint  = var.redis.source == "local-model" ? var.redis.endpoint : null
    offer_url = var.redis.source == "cross-model" ? var.redis.url : null
  }
}

# The API/backend is required for the frontend
resource "juju_integration" "backend_frontend" {
  count      = var.deploy_frontend ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name     = juju_application.backend.name
    endpoint = "test-observer-rest-api"
  }

  application {
    name     = juju_application.frontend[0].name
    endpoint = "test-observer-rest-api"
  }
}

resource "juju_integration" "backend_network" {
  count      = contains(keys(var.network_endpoint_providers), "backend") ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.backend.name
  }

  application {
    name      = var.network_endpoint_providers["backend"].source == "local-model" ? var.network_endpoint_providers["backend"].name : null
    endpoint  = var.network_endpoint_providers["backend"].source == "local-model" ? var.network_endpoint_providers["backend"].endpoint : null
    offer_url = var.network_endpoint_providers["backend"].source == "cross-model" ? var.network_endpoint_providers["backend"].url : null
  }
}

resource "juju_integration" "frontend_network" {
  count      = (var.deploy_frontend && contains(keys(var.network_endpoint_providers), "frontend")) ? 1 : 0
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.frontend[0].name
  }

  application {
    name      = var.network_endpoint_providers["frontend"].source == "local-model" ? var.network_endpoint_providers["frontend"].name : null
    endpoint  = var.network_endpoint_providers["frontend"].source == "local-model" ? var.network_endpoint_providers["frontend"].endpoint : null
    offer_url = var.network_endpoint_providers["frontend"].source == "cross-model" ? var.network_endpoint_providers["frontend"].url : null
  }
}
