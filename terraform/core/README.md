## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5 |
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | ~> 1.5.0 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_juju"></a> [juju](#provider\_juju) | ~> 1.5.0 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [juju_application.backend](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.frontend](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_integration.backend_database](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.backend_frontend](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.backend_network](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.backend_redis](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.frontend_network](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_model.model](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_backend"></a> [backend](#input\_backend) | The Test Observer API/backend application | <pre>object({<br/>    name     = string<br/>    base     = optional(string, "ubuntu@22.04")<br/>    channel  = optional(string)<br/>    config   = map(string)<br/>    image    = optional(string, "ghcr.io/canonical/test_observer/api:latest")<br/>    revision = optional(number)<br/>    units    = optional(number, 3)<br/>  })</pre> | n/a | yes |
| <a name="input_database"></a> [database](#input\_database) | The API/backend database relation information | <pre>object({<br/>    endpoint = optional(string, null)<br/>    name     = optional(string, null)<br/>    source   = string<br/>    url      = optional(string, null)<br/>  })</pre> | n/a | yes |
| <a name="input_deploy_frontend"></a> [deploy\_frontend](#input\_deploy\_frontend) | Whether to deploy the Test Observer frontend charm | `bool` | `true` | no |
| <a name="input_frontend"></a> [frontend](#input\_frontend) | The Test Observer frontend application | <pre>object({<br/>    name     = string<br/>    base     = optional(string, "ubuntu@22.04")<br/>    channel  = optional(string)<br/>    config   = map(string)<br/>    image    = optional(string, "ghcr.io/canonical/test_observer/frontend:latest")<br/>    revision = optional(number)<br/>    units    = optional(number, 3)<br/>  })</pre> | `null` | no |
| <a name="input_juju_model_uuid"></a> [juju\_model\_uuid](#input\_juju\_model\_uuid) | UUID of the Juju model to deploy to | `string` | n/a | yes |
| <a name="input_network_endpoint_providers"></a> [network\_endpoint\_providers](#input\_network\_endpoint\_providers) | The network endpoint provider relation information for the backend and frontend | <pre>map(object({<br/>    endpoint = optional(string, null)<br/>    name     = optional(string, null)<br/>    source   = string<br/>    url      = optional(string, null)<br/>  }))</pre> | `{}` | no |
| <a name="input_redis"></a> [redis](#input\_redis) | The redis relation information | <pre>object({<br/>    endpoint = optional(string, null)<br/>    name     = optional(string, null)<br/>    source   = string<br/>    url      = optional(string, null)<br/>  })</pre> | n/a | yes |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_backend_name"></a> [backend\_name](#output\_backend\_name) | The name of the backend application from the test-observer-api charm |
| <a name="output_frontend_name"></a> [frontend\_name](#output\_frontend\_name) | The name of the frontend application from the test-observer-frontend charm |
