#remote_state {
#  backend = "s3"
#  config = {
#    bucket = "<Your-bucket>"
#    key    = "${path_relative_to_include()}/terraform.tfstate"
#    region = "<Your-region>"
#  }
#}

locals {
  model_name                      = get_env("TO_MODEL_NAME", "test-observer-dev")
  cloudflare_dns_api_token        = get_env("TO_CLOUDFLARE_DNS_API_TOKEN", "")
  cloudflare_zone_read_api_token  = get_env("TO_CLOUDFLARE_ZONE_READ_API_TOKEN", "")
  cloudflare_email                = get_env("TO_CLOUDFLARE_EMAIL", "")
}

inputs = {
  model_name = local.model_name
  cloud = {
    name = "microk8s"
  }
  cloudflare_dns_api_token        = local.cloudflare_dns_api_token
  cloudflare_zone_read_api_token  = local.cloudflare_zone_read_api_token
  cloudflare_email                = local.cloudflare_email
}

terraform { source = "./modules/model.tf" }
terraform { source = "./modules/variables.tf" }
terraform { source = "./modules/applications/acme-operator.tf" }
terraform { source = "./modules/applications/ingress.tf" }
terraform { source = "./modules/applications/pg.tf" }
terraform { source = "./modules/applications/test-observer-api.tf" }
terraform { source = "./modules/applications/test-observer-fronted.tf" }
terraform { source = "./modules/integrations.tf" }

include {
  path = find_in_parent_folders()
}
