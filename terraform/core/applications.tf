# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: Apache-2.0

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
