# Copyright 2025 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

resource "juju_application" "ingress" {
  name  = "ingress"
  model_uuid = data.juju_model.model.uuid
  trust = true

  charm {
    name     = "nginx-ingress-integrator"
    channel  = "latest/stable"
    revision = 59
  }

  config = {
    tls-secret-name        = var.tls_secret_name
    whitelist-source-range = var.nginx_ingress_integrator_charm_whitelist_source_range
  }
}

resource "juju_application" "pg" {
  name  = "db"
  model_uuid = data.juju_model.model.uuid
  trust = true

  charm {
    name     = "postgresql-k8s"
    channel  = "14/stable"
    base     = "ubuntu@22.04"
    revision = 281
  }

  config = {
    # NOTE: idle_in_transaction_session_timeout is not exposed by postgresql-k8s 14/stable
    # It must be set manually via: ALTER SYSTEM SET idle_in_transaction_session_timeout = '10min';

    # Log queries taking longer than 1 second (in milliseconds)
    # Helps identify performance bottlenecks
    logging_log_min_duration_statement = 1000

    # Log when queries wait for locks
    # Helps identify blocking queries
    logging_log_lock_waits = true
  }
}

resource "juju_application" "backup-restoring-db" {
  name  = "backup-restoring-db"
  model_uuid = data.juju_model.model.uuid
  trust = true

  charm {
    name     = "postgresql-k8s"
    channel  = "14/stable"
    base     = "ubuntu@22.04"
    revision = 281
  }

  config = {
    # NOTE: idle_in_transaction_session_timeout is not exposed by postgresql-k8s 14/stable
    # It must be set manually via: ALTER SYSTEM SET idle_in_transaction_session_timeout = '10min';

    # Log queries taking longer than 1 second (in milliseconds)
    # Helps identify performance bottlenecks
    logging_log_min_duration_statement = 1000

    # Log when queries wait for locks
    # Helps identify blocking queries
    logging_log_lock_waits = true
  }
}

resource "juju_application" "test-observer-api" {
  name  = "api"
  model_uuid = data.juju_model.model.uuid

  charm {
    name    = "test-observer-api"
    channel = var.api_channel
    base    = "ubuntu@22.04"
  }

  config = {
    hostname              = var.api_hostname
    frontend_hostname     = var.frontend_hostname
    port                  = var.environment == "development" ? 80 : 443
    sentry_dsn            = "${local.sentry_dsn_map[var.environment]}"
    saml_idp_metadata_url = var.saml_idp_metadata_url
    saml_sp_cert          = var.saml_sp_cert
    saml_sp_key           = var.saml_sp_key
    sessions_secret       = var.sessions_secret
    ignore_permissions    = join(",", var.ignore_permissions)
    enable_issue_sync     = var.enable_issue_sync
  }

  units = 3
}

resource "juju_application" "test-observer-frontend" {
  name  = "frontend"
  model_uuid = data.juju_model.model.uuid

  charm {
    name    = "test-observer-frontend"
    channel = var.frontend_channel
    base    = "ubuntu@22.04"
  }

  config = {
    hostname                 = var.frontend_hostname
    test-observer-api-scheme = var.environment == "development" ? "http://" : "https://"
  }

  units = 3
}

resource "juju_application" "redis" {
  name  = "redis"
  model_uuid = data.juju_model.model.uuid

  charm {
    name     = "redis-k8s"
    channel  = "latest/edge"
    base     = "ubuntu@22.04"
    revision = 27
  }
}

resource "juju_application" "s3-integrator" {
  name  = "backups-s3-integrator"
  model_uuid = data.juju_model.model.uuid

  charm {
    name     = "s3-integrator"
    channel  = "latest/stable"
    revision = 77
    base     = "ubuntu@22.04"
  }

  config = {
    endpoint     = var.backups_s3_endpoint
    region       = var.backups_s3_region
    bucket       = var.backups_s3_bucket
    path         = var.backups_s3_path
    s3-uri-style = var.backups_s3_uri_style
  }
}

resource "juju_integration" "db-backups" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.pg.name
  }

  application {
    name = juju_application.s3-integrator.name
  }
}

resource "juju_integration" "db-backups-restore" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.backup-restoring-db.name
  }

  application {
    name = juju_application.s3-integrator.name
  }
}

resource "juju_integration" "test-observer-api-database-access" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.pg.name
  }
}

resource "juju_integration" "test-observer-frontend-to-rest-api-access" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.test-observer-frontend.name
  }
}

resource "juju_integration" "test-observer-frontend-ingress" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-frontend.name
  }

  application {
    name = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-api-ingress" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.ingress.name
  }
}


resource "juju_integration" "test-observer-redis-access" {
  model_uuid = data.juju_model.model.uuid

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.redis.name
  }
}
