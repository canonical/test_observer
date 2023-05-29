# This is a fully configured provider containing all the 
# relevant information to connect to a Juju controller.
# This information can be collected by checking the local
# juju folder (~/.local/share/juju/), or by querying the
# controller using `juju show-controller --show-password`.
# If you have already installed and configured a local
# Juju CLI or prefer to use a configuration using environment
# variables, you can use an empty provider. See the next
# example for more details.

#provider "juju" {
#  controller_addresses = "10.225.205.241:17070,10.225.205.242:17070"
#
#  username = "jujuuser"
#  password = "password1"
#
#  ca_certificate = file("~/ca-cert.pem")
#}


# When an empty provider is indicated, the Juju
# provider automatically sets the corresponding values
# by checking:
# **First**: the following environment variables that correspond
# to the configuration fields indicated above.
# JUJU_CONTROLLER_ADDRESSES
# JUJU_USERNAME
# JUJU_PASSWORD
# JUJU_CA_CERT
# **Second**: by using a locally installed Juju CLI client.
# This is the most straight-forward solution. Remember, that
# it will use the configuration used by the CLI at that 
# moment. The fields are populated using the output
# from running the command:
# `juju show-controller --show-password`

terraform {
  required_providers {
    juju = {
      version = "~> 0.7.0"
      source  = "juju/juju"
    }
  }
}

provider "juju" {}

resource "juju_model" "test-observer" {
  name = var.model_name

  dynamic "cloud" {
    for_each = [var.cloud]
    content {
      name = cloud.value["name"]
      // access more properties as needed
    }
  }
}
