data "juju_secret" "lego_creds" {
  name  = "lego-creds"
  model = var.juju_model
}