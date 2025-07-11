data "juju_secret" "lego_credentials" {
  name  = "lego-credentials"
  model = var.juju_model
}
