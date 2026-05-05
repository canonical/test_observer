## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_juju"></a> [juju](#requirement\_juju) | >=1.0.0, <2.0.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_juju"></a> [juju](#provider\_juju) | 1.5.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [juju_application.backup-db](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.database](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.otelcol](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.redis](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.s3-integrator](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.test-observer-api](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_application.test-observer-frontend](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/application) | resource |
| [juju_integration.db-backups](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.db-backups-restore](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.otel-api](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.otelcol_prod_cos](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-api-database-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-api-external-database-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-frontend-to-rest-api-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_integration.test-observer-redis-access](https://registry.terraform.io/providers/juju/juju/latest/docs/resources/integration) | resource |
| [juju_model.model](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/model) | data source |
| [juju_offer.cos_offers](https://registry.terraform.io/providers/juju/juju/latest/docs/data-sources/offer) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_api_config"></a> [api\_config](#input\_api\_config) | Full configuration for the test observer API | <pre>object({<br/>    name     = string<br/>    channel  = optional(string)<br/>    base     = optional(string, "ubuntu@22.04")<br/>    units    = optional(number, 3)<br/>    config   = map(string)<br/>    revision = optional(number)<br/>  })</pre> | n/a | yes |
| <a name="input_cos_offers"></a> [cos\_offers](#input\_cos\_offers) | Map of COS offers to integrate with, keyed by the application name to integrate with. The value should be the offer URL for the COS offer. | <pre>object({<br/>    loki    = optional(string)<br/>    tempo   = optional(string)<br/>    mimir   = optional(string)<br/>    grafana = optional(string)<br/>  })</pre> | `null` | no |
| <a name="input_database_config"></a> [database\_config](#input\_database\_config) | Full configuration for the test observer database, if not external | <pre>object({<br/>    name     = string<br/>    channel  = string<br/>    base     = optional(string, "ubuntu@22.04")<br/>    units    = number<br/>    config   = map(string)<br/>    revision = optional(number)<br/>  })</pre> | `null` | no |
| <a name="input_deploy_database"></a> [deploy\_database](#input\_deploy\_database) | Deploy a database with the api | `bool` | `true` | no |
| <a name="input_deploy_test_observer_frontend"></a> [deploy\_test\_observer\_frontend](#input\_deploy\_test\_observer\_frontend) | Deploy the test observer frontend | `bool` | `true` | no |
| <a name="input_enable_backups"></a> [enable\_backups](#input\_enable\_backups) | Enable database backups | `bool` | `false` | no |
| <a name="input_external_database_url"></a> [external\_database\_url](#input\_external\_database\_url) | URL of external database charm endpoint to relate to | `string` | `null` | no |
| <a name="input_frontend_config"></a> [frontend\_config](#input\_frontend\_config) | Full configuration for the test observer front end | <pre>object({<br/>    name     = string<br/>    channel  = optional(string)<br/>    base     = optional(string, "ubuntu@22.04")<br/>    units    = optional(number, 3)<br/>    config   = map(string)<br/>    revision = optional(number)<br/>  })</pre> | `null` | no |
| <a name="input_juju_model_uuid"></a> [juju\_model\_uuid](#input\_juju\_model\_uuid) | UUID of the Juju model to deploy to | `string` | n/a | yes |
| <a name="input_otelcol_config"></a> [otelcol\_config](#input\_otelcol\_config) | OTel Collector config to use for the charm. | <pre>object({<br/>    channel  = optional(string, "2/stable")<br/>    revision = optional(number)<br/>    base     = optional(string, "ubuntu@22.04")<br/>    config   = optional(map(string))<br/>  })</pre> | `null` | no |
| <a name="input_s3_backups_config"></a> [s3\_backups\_config](#input\_s3\_backups\_config) | Configuration of the S3 buckets backups are stored in | <pre>object({<br/>    name     = string<br/>    channel  = optional(string, "latest/stable")<br/>    base     = optional(string, "ubuntu@22.04")<br/>    revision = optional(number)<br/>    config = object({<br/>      endpoint     = string<br/>      region       = string<br/>      bucket       = string<br/>      path         = string<br/>      s3_uri_style = string<br/>    })<br/>  })</pre> | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_backup_db_name"></a> [backup\_db\_name](#output\_backup\_db\_name) | Name of the backup-db application |
| <a name="output_database_name"></a> [database\_name](#output\_database\_name) | Name of the database application |
| <a name="output_otelcol_name"></a> [otelcol\_name](#output\_otelcol\_name) | Name of the otelcol application |
| <a name="output_redis_name"></a> [redis\_name](#output\_redis\_name) | Name of the redis application |
| <a name="output_s3_integrator_name"></a> [s3\_integrator\_name](#output\_s3\_integrator\_name) | Name of the s3-integrator application |
| <a name="output_test_observer_api_name"></a> [test\_observer\_api\_name](#output\_test\_observer\_api\_name) | Name of the test-observer-api application |
| <a name="output_test_observer_frontend_name"></a> [test\_observer\_frontend\_name](#output\_test\_observer\_frontend\_name) | Name of the test-observer-frontend application |
