## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | ~> 1.3 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | 1.3.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [juju_application.backup-restoring-db](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.ingress](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.pg](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.redis](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.s3-integrator](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.test-observer-api](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.test-observer-frontend](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_integration.db-backups](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.db-backups-restore](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-api-database-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-api-ingress](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-frontend-ingress](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-frontend-to-rest-api-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-redis-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_model.model](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_api_channel"></a> [api\_channel](#input\_api\_channel) | Charmhub channel for the API charm (e.g., 'latest/edge', 'latest/edge/testing-branch') | `string` | `"latest/edge"` | no |
| <a name="input_api_hostname"></a> [api\_hostname](#input\_api\_hostname) | Test Observer API hostname | `string` | n/a | yes |
| <a name="input_backups_s3_bucket"></a> [backups\_s3\_bucket](#input\_backups\_s3\_bucket) | Database backups s3-integrator bucket | `string` | `""` | no |
| <a name="input_backups_s3_endpoint"></a> [backups\_s3\_endpoint](#input\_backups\_s3\_endpoint) | Database backups s3-integrator endpoint | `string` | `""` | no |
| <a name="input_backups_s3_path"></a> [backups\_s3\_path](#input\_backups\_s3\_path) | Database backups s3-integrator path | `string` | `""` | no |
| <a name="input_backups_s3_region"></a> [backups\_s3\_region](#input\_backups\_s3\_region) | Database backups s3-integrator region | `string` | `""` | no |
| <a name="input_backups_s3_uri_style"></a> [backups\_s3\_uri\_style](#input\_backups\_s3\_uri\_style) | Database backups s3-integrator uri\_style | `string` | `"path"` | no |
| <a name="input_enable_issue_sync"></a> [enable\_issue\_sync](#input\_enable\_issue\_sync) | Whether to enable periodic syncing of issues from GitHub, Jira, and Launchpad | `bool` | `false` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | The environment to deploy to (development, stg, production) | `any` | n/a | yes |
| <a name="input_frontend_channel"></a> [frontend\_channel](#input\_frontend\_channel) | Charmhub channel for the frontend charm (e.g., 'latest/edge', 'latest/edge/testing-branch') | `string` | `"latest/edge"` | no |
| <a name="input_frontend_hostname"></a> [frontend\_hostname](#input\_frontend\_hostname) | Test Observer front-end hostname | `string` | n/a | yes |
| <a name="input_ignore_permissions"></a> [ignore\_permissions](#input\_ignore\_permissions) | List of API permissions to ignore for all requests | `list(string)` | n/a | yes |
| <a name="input_nginx_ingress_integrator_charm_whitelist_source_range"></a> [nginx\_ingress\_integrator\_charm\_whitelist\_source\_range](#input\_nginx\_ingress\_integrator\_charm\_whitelist\_source\_range) | Allowed client IP source ranges. The value is a comma separated list of CIDRs. | `string` | `""` | no |
| <a name="input_saml_idp_metadata_url"></a> [saml\_idp\_metadata\_url](#input\_saml\_idp\_metadata\_url) | SAML metadata endpoint for the identity provider | `string` | n/a | yes |
| <a name="input_saml_sp_cert"></a> [saml\_sp\_cert](#input\_saml\_sp\_cert) | SAML service provider X.509 certificate | `string` | n/a | yes |
| <a name="input_saml_sp_key"></a> [saml\_sp\_key](#input\_saml\_sp\_key) | SAML service provider certificate private key | `string` | n/a | yes |
| <a name="input_sessions_secret"></a> [sessions\_secret](#input\_sessions\_secret) | Randomly generated secret key to use for signing session cookies | `string` | n/a | yes |
| <a name="input_tls_secret_name"></a> [tls\_secret\_name](#input\_tls\_secret\_name) | Secret where the TLS certificate for ingress is stored | `string` | `""` | no |

## Outputs

No outputs.
