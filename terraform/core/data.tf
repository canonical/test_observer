data "juju_model" "model" {
  uuid = var.juju_model_uuid
}

data "juju_offer" "cos_offers" {
  for_each = { for k, v in coalesce(var.cos_offers, {}) : k => v if v != null }
  url      = each.value
}
