output "backend_name" {
  description = "The name of the backend application from the test-observer-api charm"
  value       = juju_application.backend.name
}

output "frontend_name" {
  description = "The name of the frontend application from the test-observer-frontend charm"
  value       = one(juju_application.frontend[*].name)
}
