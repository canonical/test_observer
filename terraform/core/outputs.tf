output "test_observer_api_name" {
  description = "Name of the test-observer-api application"
  value       = juju_application.test-observer-api.name
}

output "test_observer_frontend_name" {
  description = "Name of the test-observer-frontend application"
  value       = var.deploy_test_observer_frontend ? juju_application.test-observer-frontend[0].name : null
}

output "database_name" {
  description = "Name of the database application"
  value       = var.deploy_database ? juju_application.database[0].name : null
}

output "backup_db_name" {
  description = "Name of the backup-db application"
  value       = var.enable_backups ? juju_application.backup-db[0].name : null
}

output "redis_name" {
  description = "Name of the redis application"
  value       = juju_application.redis.name
}

output "s3_integrator_name" {
  description = "Name of the s3-integrator application"
  value       = var.enable_backups ? juju_application.s3-integrator[0].name : null
}

output "otelcol_name" {
  description = "Name of the otelcol application"
  value       = var.cos_offers != null ? juju_application.otelcol[0].name : null
}
