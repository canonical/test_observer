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

resource "juju_application" "api_ingress" {
  name  = "api-ingress"
  model = var.juju_model
  trust = true

  charm {
    name     = "nginx-ingress-integrator"
    channel  = "latest/stable"
    revision = 153
  }

  config = {
    service-hostname       = var.api_hostname
    whitelist-source-range = var.nginx_ingress_integrator_charm_whitelist_source_range
  }
}

resource "juju_application" "frontend_ingress" {
  name  = "frontend-ingress"
  model = var.juju_model
  trust = true

  charm {
    name     = "nginx-ingress-integrator"
    channel  = "latest/stable"
    revision = 153
  }

  config = {
    service-hostname       = var.frontend_hostname
    whitelist-source-range = var.nginx_ingress_integrator_charm_whitelist_source_range
  }
}

resource "juju_application" "api_ingress_lego" {
  name  = "api-ingress-lego"
  model = var.juju_model
  trust = true

  charm {
    name     = "lego"
    channel  = "4/stable"
    revision = 61
  }

  config = {
    email                   = var.lego_email
    plugin                  = var.lego_plugin
    plugin-config-secret-id = data.juju_secret.lego_credentials.secret_id
  }
}

resource "juju_application" "frontend_ingress_lego" {
  name  = "frontend-ingress-lego"
  model = var.juju_model
  trust = true

  charm {
    name     = "lego"
    channel  = "4/stable"
    revision = 61
  }

  config = {
    email                   = var.lego_email
    plugin                  = var.lego_plugin
    plugin-config-secret-id = data.juju_secret.lego_credentials.secret_id
  }
}

resource "juju_access_secret" "lego_credentials_access" {
  applications = [
    juju_application.api_ingress_lego.name,
    juju_application.frontend_ingress_lego.name,
  ]
  model     = var.juju_model
  secret_id = data.juju_secret.lego_credentials.secret_id
}

resource "juju_application" "pg" {
  name  = "db"
  model = var.juju_model
  trust = true

  charm {
    name     = "postgresql-k8s"
    channel  = "14/stable"
    base     = "ubuntu@22.04"
    revision = 495
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

  storage_directives = {
    pgdata = var.pg_storage_size
  }
}

resource "juju_application" "test-observer-api" {
  name  = "api"
  model = var.juju_model

  charm {
    name    = "test-observer-api"
    channel = var.api_channel
    base    = "ubuntu@22.04"
  }

  config = {
    hostname              = var.api_hostname
    frontend_hostname     = var.frontend_hostname
    port                  = var.api_port
    sentry_dsn            = var.sentry_dsn
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
  model = var.juju_model

  charm {
    name    = "test-observer-frontend"
    channel = var.frontend_channel
    base    = "ubuntu@22.04"
  }

  config = {
    hostname                 = var.frontend_hostname
    frontend-config          = var.frontend_config
    test-observer-api-scheme = var.api_scheme
  }

  units = 3
}

resource "juju_application" "redis" {
  name  = "redis"
  model = var.juju_model

  charm {
    name     = "redis-k8s"
    channel  = "latest/edge"
    base     = "ubuntu@22.04"
    revision = 27
  }
}

resource "juju_application" "main-s3-integrator" {
  name  = "main-s3-integrator"
  model = var.juju_model

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
  model = var.juju_model

  application {
    name = juju_application.pg.name
  }

  application {
    name = juju_application.main-s3-integrator.name
  }
}

resource "juju_integration" "test-observer-api-database-access" {
  model = var.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.pg.name
  }
}

resource "juju_integration" "test-observer-frontend-to-rest-api-access" {
  model = var.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.test-observer-frontend.name
  }
}

resource "juju_integration" "test-observer-frontend-ingress" {
  model = var.juju_model

  application {
    name = juju_application.test-observer-frontend.name
  }

  application {
    name = juju_application.frontend_ingress.name
  }
}

resource "juju_integration" "test-observer-api-ingress" {
  model = var.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.api_ingress.name
  }
}

resource "juju_integration" "test-observer-api-ingress-lego" {
  model = var.juju_model

  application {
    name = juju_application.api_ingress.name
  }

  application {
    name = juju_application.api_ingress_lego.name
  }
}

resource "juju_integration" "test-observer-fronted-ingress-lego" {
  model = var.juju_model

  application {
    name = juju_application.frontend_ingress.name
  }

  application {
    name = juju_application.frontend_ingress_lego.name
  }
}

resource "juju_integration" "test-observer-redis-access" {
  model = var.juju_model

  application {
    name = juju_application.test-observer-api.name
  }

  application {
    name = juju_application.redis.name
  }
}
