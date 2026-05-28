# Copyright 2026 Canonical Ltd.
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

locals {
  cos_endpoint_map = {
    grafana = "grafana-dashboards-provider"
    mimir   = "send-remote-write"
    loki    = "send-loki-logs"
    tempo   = "send-traces"
  }

  otelcol_relations = {
    grafana_dashboard = {
      app_endpoint     = "grafana-dashboard"
      otelcol_endpoint = "grafana-dashboards-consumer"
    }

    metrics = {
      app_endpoint     = "metrics-endpoint"
      otelcol_endpoint = "metrics-endpoint"
    }
  }
}
