locals {
  cos_endpoint_map = {
    grafana = "grafana-dashboards-provider"
    mimir   = "send-remote-write"
    loki    = "send-loki-logs"
    tempo   = "send-traces"
  }
}