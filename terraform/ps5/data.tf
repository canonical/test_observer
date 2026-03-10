data "juju_model" "model" {
  name = local.juju_model.name
  owner = local.juju_model.owner
}