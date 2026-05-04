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
