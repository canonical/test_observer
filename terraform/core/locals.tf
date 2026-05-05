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
